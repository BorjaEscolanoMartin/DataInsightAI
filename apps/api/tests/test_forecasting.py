import logging
import math
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd
import pytest
from statsmodels.tsa import holtwinters  # type: ignore[import-untyped]

from app.services.forecasting import daily_series, run_forecast

START = date(2024, 1, 1)
DAYS = 60
WEEKLY = [0, 5, 10, 8, 3, -4, -6]


def _daily_csv(days: int = DAYS) -> bytes:
    rows = ["fecha,ventas"]
    for i in range(days):
        rows.append(f"{START + timedelta(days=i)},{100 + 2 * i + WEEKLY[i % 7]}")
    return ("\n".join(rows) + "\n").encode()


def test_forecast_returns_points_for_each_day_of_the_horizon():
    result = run_forecast(_daily_csv(), "fecha", "ventas")

    last = START + timedelta(days=DAYS - 1)
    expected_days = [str(last + timedelta(days=i)) for i in range(1, 31)]
    assert [p["ds"] for p in result["points"]] == expected_days
    for p in result["points"]:
        assert math.isfinite(p["yhat"])
        assert p["yhat_lower"] <= p["yhat"] <= p["yhat_upper"]
    assert isinstance(result["wape"], float)
    assert isinstance(result["mae"], float)
    assert "mape" not in result
    assert result["frequency"] == "D"
    assert result["horizon"] == 30
    assert "horizon_days" not in result


def _fail_fit_when(
    monkeypatch: pytest.MonkeyPatch, fails: Callable[[int, dict], bool]
) -> None:
    """Make Holt-Winters fit raise ValueError('boom') when fails(len(series), kwargs) holds."""
    real = holtwinters.ExponentialSmoothing

    class FlakyExponentialSmoothing:
        def __init__(self, endog, **kwargs):
            self._endog = endog
            self._kwargs = kwargs

        def fit(self, **fit_kwargs):
            if fails(len(self._endog), self._kwargs):
                raise ValueError("boom")
            return real(self._endog, **self._kwargs).fit(**fit_kwargs)

    monkeypatch.setattr(holtwinters, "ExponentialSmoothing", FlakyExponentialSmoothing)


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == "app.services.forecasting" and r.levelno == logging.WARNING
    ]


def test_logs_a_warning_for_each_failed_fit(monkeypatch, caplog):
    _fail_fit_when(monkeypatch, lambda n, kwargs: True)

    with caplog.at_level(logging.WARNING, logger="app.services.forecasting"):
        result = run_forecast(_daily_csv(), "fecha", "ventas")

    assert _warnings(caplog) == [
        "Forecast backtest failed (trend=add, seasonal=add, seasonal_periods=7): "
        "ValueError('boom')",
        "Forecast fit failed (trend=add, seasonal=add, seasonal_periods=7): ValueError('boom')",
        "Forecast fit failed (trend=add, seasonal=None, seasonal_periods=None): "
        "ValueError('boom')",
        "Forecast fit failed (trend=None, seasonal=None, seasonal_periods=None): "
        "ValueError('boom')",
    ]
    assert result["points"] == []
    assert result["wape"] is None
    assert result["mae"] is None


def test_failed_backtest_logs_a_warning_and_leaves_the_metrics_empty(monkeypatch, caplog):
    _fail_fit_when(monkeypatch, lambda n, kwargs: n < DAYS)

    with caplog.at_level(logging.WARNING, logger="app.services.forecasting"):
        result = run_forecast(_daily_csv(), "fecha", "ventas")

    assert _warnings(caplog) == [
        "Forecast backtest failed (trend=add, seasonal=add, seasonal_periods=7): "
        "ValueError('boom')",
    ]
    assert result["wape"] is None
    assert result["mae"] is None
    assert len(result["points"]) == 30


def test_falls_back_to_a_simpler_config_when_the_seasonal_fit_fails(monkeypatch, caplog):
    _fail_fit_when(monkeypatch, lambda n, kwargs: n == DAYS and kwargs["seasonal"] == "add")

    with caplog.at_level(logging.WARNING, logger="app.services.forecasting"):
        result = run_forecast(_daily_csv(), "fecha", "ventas")

    assert _warnings(caplog) == [
        "Forecast fit failed (trend=add, seasonal=add, seasonal_periods=7): ValueError('boom')",
    ]
    assert len(result["points"]) == 30
    assert isinstance(result["wape"], float)


def test_series_shorter_than_ten_days_returns_no_points():
    result = run_forecast(_daily_csv(days=9), "fecha", "ventas")

    assert result == {"target_column": "ventas", "date_column": "fecha", "points": []}


def test_series_of_ten_days_returns_points():
    result = run_forecast(_daily_csv(days=10), "fecha", "ventas")

    assert len(result["points"]) == 30


def _csv(rows: list[tuple[Any, float]]) -> bytes:
    return ("fecha,ventas\n" + "".join(f"{d},{v}\n" for d, v in rows)).encode()


def _days(count: int, start: date = START) -> list[date]:
    return [start + timedelta(days=i) for i in range(count)]


def test_unique_dates_are_not_aggregated():
    result = run_forecast(_daily_csv(), "fecha", "ventas")

    assert result["aggregation"] == "none"


def test_repeated_dates_are_summed():
    rows = [(d, v) for d in _days(40) for v in (40, 60)]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result["aggregation"] == "sum"
    assert result["points"][0]["yhat"] == pytest.approx(100, abs=1)


def test_times_of_day_are_reduced_to_their_day_before_summing():
    rows = [(f"{d} {t}", v) for d in _days(40) for t, v in (("09:00", 40), ("17:30", 60))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result["aggregation"] == "sum"
    assert result["frequency"] == "D"
    assert result["points"][0]["ds"] == str(START + timedelta(days=40))
    assert result["points"][0]["yhat"] == pytest.approx(100, abs=1)


def _months_end(count: int) -> list[date]:
    ends = pd.date_range("2022-01-31", periods=count, freq="ME")
    return [d.date() for d in ends]


FREQUENCY_CASES = {
    # frequency: (dates, seasonal_periods of the full fit, horizon dates)
    "D": (
        _days(60), 7, [str(START + timedelta(days=60 + i)) for i in range(30)],
    ),
    "W": (
        [START + timedelta(weeks=i) for i in range(60)], None,
        [str(START + timedelta(weeks=60 + i)) for i in range(12)],
    ),
    "M": (
        _months_end(36), 12, [f"2025-{m:02d}-01" for m in range(1, 13)],
    ),
    "Q": (
        [date(2021 + i // 4, 1 + 3 * (i % 4), 1) for i in range(16)], 4,
        [f"{2025 + i // 4}-{1 + 3 * (i % 4):02d}-01" for i in range(8)],
    ),
    "Y": (
        [date(2010 + i, 1, 1) for i in range(12)], None,
        ["2022-01-01", "2023-01-01", "2024-01-01"],
    ),
}


@pytest.fixture
def fits(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, dict]]:
    """Record (series length, constructor kwargs) of every Holt-Winters model."""
    real = holtwinters.ExponentialSmoothing
    calls: list[tuple[int, dict]] = []

    def spy(endog, **kwargs):
        calls.append((len(endog), kwargs))
        return real(endog, **kwargs)

    monkeypatch.setattr(holtwinters, "ExponentialSmoothing", spy)
    return calls


@pytest.mark.parametrize("frequency", FREQUENCY_CASES)
def test_frequency_sets_the_season_and_the_horizon(frequency, fits):
    dates, seasonal_periods, horizon_dates = FREQUENCY_CASES[frequency]
    rows = [(d, 100 + 2 * i + WEEKLY[i % 7]) for i, d in enumerate(dates)]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result["frequency"] == frequency
    assert result["horizon"] == len(horizon_dates)
    assert [p["ds"] for p in result["points"]] == horizon_dates
    full_fit = next(kwargs for n, kwargs in fits if n == len(dates))
    assert full_fit["seasonal_periods"] == seasonal_periods


def test_irregular_spacing_gives_no_forecast(caplog):
    rows = [(START + timedelta(days=3 * i), 100 + i) for i in range(30)]

    with caplog.at_level(logging.WARNING, logger="app.services.forecasting"):
        result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result == {"target_column": "ventas", "date_column": "fecha", "points": []}
    assert _warnings(caplog) == ["Forecast skipped: irregular date spacing (median 3 days)"]


def test_two_dates_in_the_same_period_give_no_forecast(caplog):
    # Monthly spacing, but two dates fall in March 2023.
    dates = _months_end(24)
    dates.insert(14, date(2023, 3, 15))

    with caplog.at_level(logging.WARNING, logger="app.services.forecasting"):
        result = run_forecast(_csv([(d, 100 + i) for i, d in enumerate(dates)]), "fecha", "ventas")

    assert result["points"] == []
    assert _warnings(caplog) == ["Forecast skipped: two dates in the same period (M)"]


def _with_gap(days_before: int, gap: int, days_after: int) -> list[date]:
    return _days(days_before) + _days(days_after, START + timedelta(days=days_before + gap))


def test_a_gap_of_three_steps_is_short_and_keeps_the_whole_series():
    rows = [(d, 100 + i) for i, d in enumerate(_with_gap(30, 3, 9))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    assert len(result["points"]) == 30


def test_a_gap_of_four_steps_is_long_and_keeps_only_the_series_after_it(caplog):
    # Nine days after the gap are fewer than the ten a forecast needs.
    rows = [(d, 100 + i) for i, d in enumerate(_with_gap(30, 4, 9))]

    with caplog.at_level(logging.WARNING, logger="app.services.forecasting"):
        result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result == {"target_column": "ventas", "date_column": "fecha", "points": []}
    assert _warnings(caplog) == ["Forecast skipped: 9 points after the last long gap"]


def test_short_gaps_are_interpolated_when_nothing_was_summed():
    dates = _with_gap(37, 3, 3)

    result = run_forecast(_csv([(d, 100) for d in dates]), "fecha", "ventas")

    # The weekly season would carry three low weekdays if the gap had been filled with 0.
    first_week = [p["yhat"] for p in result["points"][:7]]
    assert first_week == pytest.approx([100] * 7, abs=1)


def test_short_gaps_are_zero_when_dates_were_summed():
    # Three days without any transaction mean three days without sales.
    dates = _with_gap(37, 3, 3)
    rows = [(d, v) for d in dates for v in (40, 60)]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    # The weekly season learns the three empty weekdays.
    first_week = [p["yhat"] for p in result["points"][:7]]
    assert sum(y < 90 for y in first_week) == 3


@pytest.mark.parametrize(("days", "seasonal_periods"), [(20, None), (21, 7)])
def test_the_season_needs_three_full_seasons(days, seasonal_periods, fits):
    run_forecast(_daily_csv(days), "fecha", "ventas")

    full_fit = next(kwargs for n, kwargs in fits if n == days)
    assert full_fit["seasonal_periods"] == seasonal_periods


def _forecast_always(monkeypatch: pytest.MonkeyPatch, value: float) -> None:
    """Replace Holt-Winters with a model that always forecasts `value`."""

    class ConstantModel:
        def __init__(self, endog, **kwargs):
            pass

        def fit(self, **fit_kwargs):
            return self

        def forecast(self, steps):
            return np.full(steps, value)

        def simulate(self, nsimulations, repetitions, **kwargs):
            return np.full((nsimulations, repetitions), value)

    monkeypatch.setattr(holtwinters, "ExponentialSmoothing", ConstantModel)


def test_backtest_reports_wape_and_mae(monkeypatch):
    # 60 days: the backtest holds the last 12, alternating 100 and 120; the model says 100.
    _forecast_always(monkeypatch, 100)
    rows = [(d, 100 + 20 * (i % 2)) for i, d in enumerate(_days(60))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    # Six errors of 20 over actual values that add up to 1,320.
    assert result["wape"] == pytest.approx(120 / 1320 * 100)
    assert result["mae"] == pytest.approx(10)


def test_wape_divides_by_the_absolute_actual_values(monkeypatch):
    # Alternating -100 and 100 add up to 0; their absolute values add up to 1,200.
    _forecast_always(monkeypatch, 0)
    rows = [(d, 100 * (-1) ** i) for i, d in enumerate(_days(60))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result["wape"] == pytest.approx(100)
    assert result["mae"] == pytest.approx(100)


def test_wape_is_empty_when_the_actual_values_are_all_zero(monkeypatch):
    _forecast_always(monkeypatch, 5)
    rows = [(d, 0) for d in _days(60)]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result["wape"] is None
    assert result["mae"] == pytest.approx(5)


def test_backtest_ignores_filled_steps(monkeypatch):
    # Two days without sales inside the 12-day backtest are filled with 0, not measured.
    _forecast_always(monkeypatch, 100)
    rows = [(d, v) for d in _with_gap(55, 2, 5) for v in (40, 60)]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result["wape"] == pytest.approx(0)
    assert result["mae"] == pytest.approx(0)


class SimulatedModel:
    """Forecasts 10 and simulates repetition k of every step as k - 100 (-100 to 899)."""

    simulate_calls: list[dict] = []

    def __init__(self, endog, **kwargs):
        pass

    def fit(self, **fit_kwargs):
        return self

    def forecast(self, steps):
        return np.full(steps, 10.0)

    def simulate(self, nsimulations, **kwargs):
        SimulatedModel.simulate_calls.append({"nsimulations": nsimulations, **kwargs})
        repetitions = kwargs["repetitions"]
        return np.tile(np.arange(repetitions) - 100.0, (nsimulations, 1))


@pytest.fixture
def simulated(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    SimulatedModel.simulate_calls = []
    monkeypatch.setattr(holtwinters, "ExponentialSmoothing", SimulatedModel)
    return SimulatedModel.simulate_calls


def test_interval_comes_from_1000_seeded_simulations_of_the_fitted_model(simulated):
    rows = [(d, -5 + i) for i, d in enumerate(_days(60))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    [call] = simulated
    assert call["nsimulations"] == 30
    assert call["repetitions"] == 1000
    assert call["error"] == "add"
    assert call["random_errors"] is None
    assert call["rng"].random() == np.random.default_rng(42).random()
    # 2.5 and 97.5 percentiles of -100..899; the history has a negative, so nothing is cut.
    for p in result["points"]:
        assert p["yhat"] == 10
        assert p["yhat_lower"] == pytest.approx(np.percentile(np.arange(1000) - 100.0, 2.5))
        assert p["yhat_upper"] == pytest.approx(np.percentile(np.arange(1000) - 100.0, 97.5))


def test_interval_is_cut_at_zero_when_the_history_has_no_negatives(simulated):
    rows = [(d, i) for i, d in enumerate(_days(60))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    for p in result["points"]:
        assert p["yhat_lower"] == 0
        assert p["yhat_upper"] == pytest.approx(np.percentile(np.arange(1000) - 100.0, 97.5))


def test_the_same_csv_always_gets_the_same_interval():
    first = run_forecast(_daily_csv(), "fecha", "ventas")
    second = run_forecast(_daily_csv(), "fecha", "ventas")

    assert first["points"] == second["points"]


@pytest.mark.parametrize(
    ("history_start", "expected"),
    [(0, (0, 0, 0)), (-1, (-5, -5, -5))],
    ids=["no-negatives", "with-a-negative"],
)
def test_forecast_and_interval_are_cut_at_zero_only_without_negative_history(
    monkeypatch, history_start, expected
):
    _forecast_always(monkeypatch, -5)
    rows = [(d, history_start + i) for i, d in enumerate(_days(60))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    for p in result["points"]:
        assert (p["yhat_lower"], p["yhat"], p["yhat_upper"]) == expected


def test_a_declining_series_keeps_its_forecast_inside_the_band():
    noise = np.random.default_rng(0).normal(0, 5, 100)
    rows = [(d, max(0.0, 300 - 3 * i + noise[i])) for i, d in enumerate(_days(100))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    for p in result["points"]:
        assert 0 <= p["yhat_lower"] <= p["yhat"] <= p["yhat_upper"]


def test_backtest_measures_the_forecast_cut_at_zero(monkeypatch):
    # History 0..59 has no negatives; the backtest holds 48..59 and the model says -5,
    # which is shown as 0, so the errors are the actual values themselves.
    _forecast_always(monkeypatch, -5)
    rows = [(d, i) for i, d in enumerate(_days(60))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result["wape"] == pytest.approx(100)
    assert result["mae"] == pytest.approx(sum(range(48, 60)) / 12)


def test_backtest_keeps_negative_forecasts_when_the_history_has_negatives(monkeypatch):
    # History -1..58: the -5 forecast is kept, so each error is the actual value plus 5.
    _forecast_always(monkeypatch, -5)
    rows = [(d, i - 1) for i, d in enumerate(_days(60))]

    result = run_forecast(_csv(rows), "fecha", "ventas")

    assert result["mae"] == pytest.approx(sum(range(47, 59)) / 12 + 5)


def test_daily_series_sums_repeated_days_and_keeps_single_ones():
    df = pd.DataFrame({
        "fecha": ["2024-01-02 17:30", "2024-01-01", "2024-01-02 09:00", "2024-01-03"],
        "ventas": [60, 100, 40, None],
    })

    by_day, aggregation = daily_series(df, "fecha", "ventas")

    assert aggregation == "sum"
    assert by_day.to_dict() == {pd.Timestamp("2024-01-01"): 100, pd.Timestamp("2024-01-02"): 100}


def test_daily_series_without_repeated_days_is_not_aggregated():
    df = pd.DataFrame({"fecha": ["2024-01-01", "2024-01-02"], "ventas": [1, 2]})

    by_day, aggregation = daily_series(df, "fecha", "ventas")

    assert aggregation == "none"
    assert list(by_day) == [1, 2]
