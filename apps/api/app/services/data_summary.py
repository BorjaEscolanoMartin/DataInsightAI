"""Deterministic summaries of the uploaded CSV that the insights prompt gives the model."""

import logging
from typing import Any, NamedTuple

import numpy as np
import pandas as pd

from app.services.forecasting import daily_series, detect_frequency
from app.services.numbers import format_es
from app.services.profiling import iqr_bounds
from app.services.targets import forecast_target, regression_target

logger = logging.getLogger(__name__)

MAX_PERIODS = 24
PEAKS = 3
MAX_BREAKDOWN_COLUMNS = 4
MAX_GROUPS = 10
# Numeric columns with this many distinct values or fewer are broken down like categories.
MAX_NUMERIC_GROUPS = 10
TARGET_OUTLIER_COLUMNS = 2
TARGET_OUTLIER_GROUPS = 3
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


class Group(NamedTuple):
    label: str
    n: int
    mean: float
    # Against the overall mean of the target; None when that mean is 0.
    pct: float | None


class GroupDifference(NamedTuple):
    label: str
    base_label: str
    change: float
    # Against the base group's mean; None when that mean is 0.
    pct: float | None


class ColumnBreakdown(NamedTuple):
    column: str
    groups: list[Group]
    # Only for two groups: the smaller one against the larger one.
    difference: GroupDifference | None = None


class Side(NamedTuple):
    n: int
    min: float
    max: float


class Outliers(NamedTuple):
    column: str
    low: Side | None
    high: Side | None


def summary_target(profile: dict[str, Any]) -> str | None:
    """The forecast target when there is a date column, otherwise the regression target."""
    if profile.get("date_column_candidate"):
        return forecast_target(profile)
    return regression_target(profile)


def _label(value: Any) -> str:
    """Decimal values in Spanish format with their own decimals (1,5); whole numbers stay
    plain, so a year is never written as 2.019."""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        # Positional, never scientific (1e-05): the shortest digits that give back the value.
        digits = np.format_float_positional(value, trim="-")
        return format_es(value, len(digits.split(".")[1]))
    return str(value)


def _groups(df: pd.DataFrame, column: str, target: str, overall: float) -> list[Group]:
    data = df[[column, target]].dropna()
    stats = data.groupby(column)[target].agg(["count", "mean"])
    stats = stats.sort_values("count", ascending=False, kind="stable")

    def group(label: str, n: int, mean: float) -> Group:
        return Group(label, n, mean, (mean - overall) / abs(overall) * 100 if overall else None)

    groups = [group(_label(v), int(r["count"]), float(r["mean"])) for v, r in
              stats.head(MAX_GROUPS).iterrows()]
    rest = data[data[column].isin(stats.index[MAX_GROUPS:])][target]
    if len(rest):
        groups.append(group("otros", len(rest), float(rest.mean())))
    return groups


def _sides(values: pd.Series) -> tuple[Side | None, Side | None, pd.Series]:
    bounds = iqr_bounds(values)
    if bounds is None:
        return None, None, values.iloc[0:0]

    def side(selected: pd.Series) -> Side | None:
        if selected.empty:
            return None
        return Side(len(selected), float(selected.min()), float(selected.max()))

    low, high = values[values < bounds[0]], values[values > bounds[1]]
    return side(low), side(high), pd.concat([low, high])


def _breakdown(column: str, groups: list[Group]) -> ColumnBreakdown:
    if len(groups) != 2:
        return ColumnBreakdown(column, groups)
    base, other = groups  # largest group first
    change = other.mean - base.mean
    pct = change / abs(base.mean) * 100 if base.mean else None
    return ColumnBreakdown(column, groups, GroupDifference(other.label, base.label, change, pct))


def breakdowns(df: pd.DataFrame, profile: dict[str, Any]) -> dict[str, Any] | None:
    """The target's mean per group, outliers per numeric column and the groups of the
    target's outliers; None when there is no target."""
    target = summary_target(profile)
    if target is None:
        return None
    columns = profile.get("columns", [])
    overall = float(df[target].mean())
    # A column that fails is skipped with a warning naming its position, not its CSV text; a
    # column without rows shared with the target has no groups and is left out.
    computed = []
    for index, c in enumerate(columns):
        if c["name"] == target or c.get("is_identifier") or not (
            c["type"] in ("categorical", "boolean")
            or (c["type"] == "numeric" and c.get("unique_count", 0) <= MAX_NUMERIC_GROUPS)
        ):
            continue
        try:
            groups = _groups(df, c["name"], target, overall)
        except Exception as exc:
            logger.warning("Breakdown skipped column %d: %s", index, type(exc).__name__)
            continue
        if groups:
            computed.append(_breakdown(c["name"], groups))

    def spread(breakdown: ColumnBreakdown) -> float:
        means = [g.mean for g in breakdown.groups]
        return max(means) - min(means)

    ranked = sorted(computed, key=spread, reverse=True)[:MAX_BREAKDOWN_COLUMNS]

    outliers = []
    target_outlier_rows = df.index[0:0]
    for index, c in enumerate(columns):
        if c["type"] != "numeric" or c.get("is_identifier"):
            continue
        try:
            low, high, rows = _sides(df[c["name"]].dropna())
        except Exception as exc:
            logger.warning("Outliers skipped column %d: %s", index, type(exc).__name__)
            continue
        if low or high:
            outliers.append(Outliers(c["name"], low, high))
        if c["name"] == target:
            target_outlier_rows = rows.index

    target_outliers = []
    for breakdown in ranked[:TARGET_OUTLIER_COLUMNS]:
        counts = df.loc[target_outlier_rows, breakdown.column].dropna().value_counts()
        if len(counts):
            target_outliers.append((breakdown.column, [
                (_label(v), int(n)) for v, n in counts.head(TARGET_OUTLIER_GROUPS).items()
            ]))

    return {
        "target": target,
        "overall_mean": overall,
        "columns": ranked,
        "outliers": outliers,
        "target_outliers": target_outliers,
    }
