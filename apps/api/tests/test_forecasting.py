import logging
import math
from collections.abc import Callable
from datetime import date, timedelta

import pytest
from statsmodels.tsa import holtwinters  # type: ignore[import-untyped]

from app.services.forecasting import run_forecast

START = date(2024, 1, 1)
DAYS = 60
WEEKLY = [0, 5, 10, 8, 3, -4, -6]


def _daily_csv() -> bytes:
    rows = ["fecha,ventas"]
    for i in range(DAYS):
        rows.append(f"{START + timedelta(days=i)},{100 + 2 * i + WEEKLY[i % 7]}")
    return ("\n".join(rows) + "\n").encode()


def test_forecast_returns_points_for_each_day_of_the_horizon():
    result = run_forecast(_daily_csv(), "fecha", "ventas", horizon_days=30)

    last = START + timedelta(days=DAYS - 1)
    expected_days = [str(last + timedelta(days=i)) for i in range(1, 31)]
    assert [p["ds"] for p in result["points"]] == expected_days
    for p in result["points"]:
        assert math.isfinite(p["yhat"])
        assert p["yhat_lower"] <= p["yhat"] <= p["yhat_upper"]
    assert isinstance(result["mape"], float)
    assert result["horizon_days"] == 30


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
        result = run_forecast(_daily_csv(), "fecha", "ventas", horizon_days=30)

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
    assert result["mape"] is None


def test_failed_backtest_logs_a_warning_and_leaves_mape_empty(monkeypatch, caplog):
    _fail_fit_when(monkeypatch, lambda n, kwargs: n < DAYS)

    with caplog.at_level(logging.WARNING, logger="app.services.forecasting"):
        result = run_forecast(_daily_csv(), "fecha", "ventas", horizon_days=30)

    assert _warnings(caplog) == [
        "Forecast backtest failed (trend=add, seasonal=add, seasonal_periods=7): "
        "ValueError('boom')",
    ]
    assert result["mape"] is None
    assert len(result["points"]) == 30


def test_falls_back_to_a_simpler_config_when_the_seasonal_fit_fails(monkeypatch, caplog):
    _fail_fit_when(monkeypatch, lambda n, kwargs: n == DAYS and kwargs["seasonal"] == "add")

    with caplog.at_level(logging.WARNING, logger="app.services.forecasting"):
        result = run_forecast(_daily_csv(), "fecha", "ventas", horizon_days=30)

    assert _warnings(caplog) == [
        "Forecast fit failed (trend=add, seasonal=add, seasonal_periods=7): ValueError('boom')",
    ]
    assert len(result["points"]) == 30
    assert isinstance(result["mape"], float)
