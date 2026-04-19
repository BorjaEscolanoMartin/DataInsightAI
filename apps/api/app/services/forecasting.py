from __future__ import annotations

import io
import math
from typing import Any

import numpy as np
import pandas as pd


def _mape(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    mask = actual != 0
    if mask.sum() == 0:
        return None
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def run_forecast(content: bytes, date_col: str, target_col: str, horizon_days: int = 30) -> dict[str, Any]:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing  # type: ignore[import-untyped]

    df = pd.read_csv(io.BytesIO(content))
    df[date_col] = pd.to_datetime(df[date_col], format="mixed", dayfirst=False)
    df = df[[date_col, target_col]].dropna().sort_values(date_col)
    df = df.groupby(date_col, as_index=False)[target_col].mean()
    df = df.set_index(date_col).asfreq("D").interpolate()

    series = df[target_col].astype(float)
    n = len(series)

    if n < 10:
        return {"target_column": target_col, "date_column": date_col, "points": []}

    # Backtest on last 20% (min 5, max 30)
    test_size = max(5, min(30, n // 5))
    train = series.iloc[:-test_size]
    test = series.iloc[-test_size:]

    seasonal_periods = 7 if n >= 21 else None
    trend: str | None = "add" if n >= 10 else None
    seasonal: str | None = "add" if seasonal_periods and n >= seasonal_periods * 2 else None

    def _fit(s, tr, seas, sp):
        return ExponentialSmoothing(
            s,
            trend=tr,
            seasonal=seas,
            seasonal_periods=sp,
            initialization_method="estimated",
        ).fit(optimized=True, disp=False)

    mape_val: float | None = None
    try:
        model = _fit(train, trend, seasonal, seasonal_periods)
        backtest = model.forecast(test_size)
        mape_val = _mape(test.values, backtest.values)
    except Exception:
        pass

    # Full model on all data — try progressively simpler configs on failure
    forecast_vals = None
    for tr, seas, sp in [
        (trend, seasonal, seasonal_periods),
        (trend, None, None),
        (None, None, None),
    ]:
        try:
            model_full = _fit(series, tr, seas, sp)
            forecast_vals = model_full.forecast(horizon_days)
            break
        except Exception:
            continue

    if forecast_vals is None:
        return {"target_column": target_col, "date_column": date_col, "mape": mape_val, "points": []}

    last_std = float(series.tail(max(7, test_size)).std()) if n > 1 else 0.0
    ci_width = last_std * 1.96

    points = []
    for i, (ds, yhat) in enumerate(forecast_vals.items()):
        yhat_f = float(yhat)
        width = ci_width * math.sqrt(i + 1)
        points.append({
            "ds": str(ds.date()) if hasattr(ds, "date") else str(ds),
            "yhat": yhat_f,
            "yhat_lower": yhat_f - width,
            "yhat_upper": yhat_f + width,
        })

    return {
        "target_column": target_col,
        "date_column": date_col,
        "mape": mape_val,
        "horizon_days": horizon_days,
        "points": points,
    }
