from __future__ import annotations

import io
import logging
import math
from typing import Any, NamedTuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MIN_POINTS = 10
# Up to this many consecutive missing steps are filled; a longer gap cuts the series.
MAX_SHORT_GAP = 3


class _Frequency(NamedTuple):
    code: str
    min_days: float
    max_days: float
    season: int | None
    horizon: int


FREQUENCIES = (
    _Frequency("D", 1, 1, 7, 30),
    _Frequency("W", 7, 7, 52, 12),
    _Frequency("M", 28, 31, 12, 12),
    _Frequency("Q", 89, 92, 4, 8),
    _Frequency("Y", 365, 366, None, 3),
)


def _warn_fit_failed(
    stage: str, trend: str | None, seasonal: str | None, seasonal_periods: int | None,
    exc: Exception,
) -> None:
    logger.warning(
        "Forecast %s failed (trend=%s, seasonal=%s, seasonal_periods=%s): %r",
        stage, trend, seasonal, seasonal_periods, exc,
    )


def _backtest_errors(
    actual: np.ndarray, predicted: np.ndarray
) -> tuple[float | None, float | None]:
    """WAPE (%) and MAE of the backtest; WAPE is empty when the actual values are all 0."""
    if len(actual) == 0:
        return None, None
    abs_errors = np.abs(actual - predicted)
    scale = float(np.abs(actual).sum())
    wape = float(abs_errors.sum() / scale * 100) if scale else None
    return wape, float(abs_errors.mean())


def _no_forecast(target_col: str, date_col: str, reason: str) -> dict[str, Any]:
    logger.warning("Forecast skipped: %s", reason)
    return {"target_column": target_col, "date_column": date_col, "points": []}


def _detect_frequency(dates: pd.DatetimeIndex) -> tuple[_Frequency | None, float]:
    spacing = float(np.median(np.diff(dates.values) / np.timedelta64(1, "D")))
    frequency = next(
        (f for f in FREQUENCIES if f.min_days <= spacing <= f.max_days), None
    )
    return frequency, spacing


def _start_after_last_long_gap(missing: np.ndarray) -> int:
    start = run = 0
    for i, is_missing in enumerate(missing):
        run = run + 1 if is_missing else 0
        if run > MAX_SHORT_GAP:
            start = i + 1
    return start


def _seasonal_periods(frequency: _Frequency, n: int) -> int | None:
    if frequency.season and n >= 3 * frequency.season:
        return frequency.season
    return None


def run_forecast(content: bytes, date_col: str, target_col: str) -> dict[str, Any]:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing  # type: ignore[import-untyped]

    df = pd.read_csv(io.BytesIO(content))
    df[date_col] = pd.to_datetime(df[date_col], format="mixed", dayfirst=False).dt.normalize()
    df = df[[date_col, target_col]].dropna()
    aggregation = "sum" if df[date_col].duplicated().any() else "none"
    by_date = df.groupby(date_col)[target_col].sum().astype(float).sort_index()

    if len(by_date) < MIN_POINTS:
        return {"target_column": target_col, "date_column": date_col, "points": []}

    frequency, spacing = _detect_frequency(by_date.index)
    if frequency is None:
        return _no_forecast(
            target_col, date_col, f"irregular date spacing (median {spacing:g} days)"
        )
    periods = by_date.index.to_period(frequency.code)
    if periods.has_duplicates:
        return _no_forecast(
            target_col, date_col, f"two dates in the same period ({frequency.code})"
        )

    series = pd.Series(by_date.to_numpy(), index=periods).reindex(
        pd.period_range(periods.min(), periods.max(), freq=frequency.code)
    )
    series = series.iloc[_start_after_last_long_gap(series.isna().to_numpy()):]
    observed = series.notna().to_numpy()
    series = series.fillna(0) if aggregation == "sum" else series.interpolate()
    n = len(series)
    if n < MIN_POINTS:
        return _no_forecast(target_col, date_col, f"{n} points after the last long gap")

    values = series.to_numpy()
    horizon = frequency.horizon

    # Backtest on last 20% (min 5, max 30)
    test_size = max(5, min(30, n // 5))
    train = values[:-test_size]
    test = values[-test_size:]
    test_observed = observed[-test_size:]

    def _config(length: int) -> tuple[str | None, str | None, int | None]:
        seasonal_periods = _seasonal_periods(frequency, length)
        return "add", "add" if seasonal_periods else None, seasonal_periods

    def _fit(s, tr, seas, sp):
        return ExponentialSmoothing(
            s,
            trend=tr,
            seasonal=seas,
            seasonal_periods=sp,
            initialization_method="estimated",
        ).fit(optimized=True)

    wape: float | None = None
    mae: float | None = None
    trend, seasonal, seasonal_periods = _config(len(train))
    try:
        model = _fit(train, trend, seasonal, seasonal_periods)
        backtest = model.forecast(test_size)
        wape, mae = _backtest_errors(test[test_observed], backtest[test_observed])
    except Exception as exc:
        _warn_fit_failed("backtest", trend, seasonal, seasonal_periods, exc)

    # Full model on all data — try progressively simpler configs on failure
    trend, seasonal, seasonal_periods = _config(n)
    forecast_vals = None
    for tr, seas, sp in [
        (trend, seasonal, seasonal_periods),
        (trend, None, None),
        (None, None, None),
    ]:
        try:
            model_full = _fit(values, tr, seas, sp)
            forecast_vals = model_full.forecast(horizon)
            break
        except Exception as exc:
            _warn_fit_failed("fit", tr, seas, sp, exc)
            continue

    result: dict[str, Any] = {
        "target_column": target_col,
        "date_column": date_col,
        "aggregation": aggregation,
        "frequency": frequency.code,
        "horizon": horizon,
        "wape": wape,
        "mae": mae,
        "points": [],
    }
    if forecast_vals is None:
        return result

    last_std = float(series.tail(max(7, test_size)).std())
    ci_width = last_std * 1.96

    last_period = series.index[-1]
    for i, yhat in enumerate(forecast_vals):
        yhat_f = float(yhat)
        width = ci_width * math.sqrt(i + 1)
        result["points"].append({
            "ds": str((last_period + i + 1).start_time.date()),
            "yhat": yhat_f,
            "yhat_lower": yhat_f - width,
            "yhat_upper": yhat_f + width,
        })
    return result
