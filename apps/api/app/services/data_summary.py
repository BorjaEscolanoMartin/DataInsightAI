"""Deterministic summaries of the uploaded CSV that the insights prompt gives the model."""

from typing import Any, NamedTuple

import pandas as pd

from app.services.forecasting import daily_series, detect_frequency
from app.services.targets import forecast_target

MAX_PERIODS = 24
PEAKS = 3
# Daily and weekly data are averaged per month; coarser data keeps its own period.
_SUMMARY_PERIOD = {"D": "M", "W": "M", "M": "M", "Q": "Q", "Y": "Y"}
_PERIODS_PER_YEAR = {"M": 12, "Q": 4, "Y": 1}


class PeriodMean(NamedTuple):
    label: str
    mean: float
    complete: bool


class DayValue(NamedTuple):
    date: str
    value: float


class Change(NamedTuple):
    start_label: str
    end_label: str
    start: float
    end: float
    change: float
    pct: float | None


def _change(start_label: str, end_label: str, start: float, end: float) -> Change:
    pct = (end - start) / abs(start) * 100 if start else None
    return Change(start_label, end_label, start, end, end - start, pct)


def temporal_summary(df: pd.DataFrame, profile: dict[str, Any]) -> dict[str, Any] | None:
    """The forecast target per period, its extreme days and its trend; None without a date."""
    date_col = profile.get("date_column_candidate")
    target = forecast_target(profile)
    if not date_col or not target:
        return None
    by_day, aggregation = daily_series(df, date_col, target)
    if len(by_day) < 2:
        return None
    frequency, _ = detect_frequency(by_day.index)
    if frequency is None:
        return None

    period = _SUMMARY_PERIOD[frequency.code]
    means = by_day.groupby(by_day.index.to_period(period)).mean()
    # The first (last) period misses data when one more step before (after) would still fall
    # inside it. Only daily and weekly data can leave a month partly empty.
    step = pd.Timedelta(days=frequency.min_days)
    complete = pd.Series(True, index=means.index)
    if frequency.code != period:
        complete.iloc[0] = by_day.index[0] - step < means.index[0].start_time
        complete.iloc[-1] = by_day.index[-1] + step > means.index[-1].end_time
    periods = [
        PeriodMean(str(p), float(m), bool(c)) for p, m, c in zip(means.index, means, complete)
    ][-MAX_PERIODS:]

    full = [p for p in periods if p.complete]
    trend = (
        _change(full[0].label, full[-1].label, full[0].mean, full[-1].mean)
        if len(full) >= 2 else None
    )
    year = _PERIODS_PER_YEAR[period]
    year_over_year = None
    if len(full) >= 2 * year:
        before, last = full[-2 * year:-year], full[-year:]
        # Each year is named by its last period: 12 months to 2025-09 against 12 to 2026-09.
        year_over_year = _change(
            before[-1].label, last[-1].label,
            sum(p.mean for p in before) / year, sum(p.mean for p in last) / year,
        )

    def days(values: pd.Series) -> list[DayValue]:
        return [DayValue(str(d.date()), float(v)) for d, v in values.items()]

    return {
        "target": target,
        "date_column": date_col,
        "aggregation": aggregation,
        "period": period,
        "periods": periods,
        "highest": days(by_day.nlargest(PEAKS)),
        "lowest": days(by_day.nsmallest(PEAKS)),
        "trend": trend,
        "year_over_year": year_over_year,
    }
