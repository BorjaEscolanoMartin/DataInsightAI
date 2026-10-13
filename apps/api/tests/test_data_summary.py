from datetime import date, timedelta

import pandas as pd
import pytest

from app.services.data_summary import pct_change, temporal_summary

PROFILE = {
    "date_column_candidate": "fecha",
    "columns": [
        {"name": "fecha", "type": "date"},
        {"name": "ventas", "type": "numeric", "is_identifier": False},
    ],
}


def _frame(rows: list[tuple[date, float]]) -> pd.DataFrame:
    return pd.DataFrame({"fecha": [str(d) for d, _ in rows], "ventas": [v for _, v in rows]})


def _days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _month_value(d: date) -> float:
    return {1: 10, 2: 20, 3: 30, 4: 40}[d.month]


def test_daily_data_is_averaged_per_month_marking_incomplete_months():
    # Jan starts on the 15th and Apr ends on the 10th, so only Feb and Mar are complete.
    rows = [(d, _month_value(d)) for d in _days(date(2024, 1, 15), date(2024, 4, 10))]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert summary["target"] == "ventas"
    assert summary["aggregation"] == "none"
    assert summary["period"] == "M"
    assert summary["periods"] == [
        ("2024-01", 10, False),
        ("2024-02", 20, True),
        ("2024-03", 30, True),
        ("2024-04", 40, False),
    ]
    # Between the first and the last complete month.
    assert summary["trend"] == ("2024-02", "2024-03", 20, 30, 10, pytest.approx(50))
    assert summary["year_over_year"] is None


def test_repeated_days_are_summed_before_the_monthly_mean():
    rows = [(d, 5) for d in _days(date(2024, 2, 1), date(2024, 3, 31)) for _ in range(2)]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert summary["aggregation"] == "sum"
    assert [mean for _, mean, _ in summary["periods"]] == [10, 10]


def test_highest_and_lowest_days_come_with_their_date():
    days = _days(date(2024, 2, 1), date(2024, 2, 29))
    values = {date(2024, 2, 9): 900, date(2024, 2, 3): 800, date(2024, 2, 20): 700,
              date(2024, 2, 14): 1, date(2024, 2, 5): 2, date(2024, 2, 27): 3}
    rows = [(d, values.get(d, 100)) for d in days]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert summary["highest"] == [("2024-02-09", 900), ("2024-02-03", 800), ("2024-02-20", 700)]
    assert summary["lowest"] == [("2024-02-14", 1), ("2024-02-05", 2), ("2024-02-27", 3)]


def _months(count: int, start: date = date(2022, 1, 1)) -> list[date]:
    return [date(start.year + (start.month - 1 + i) // 12, (start.month - 1 + i) % 12 + 1, 1)
            for i in range(count)]


def test_monthly_data_keeps_its_period_and_only_the_last_24_months():
    rows = [(d, i) for i, d in enumerate(_months(30))]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert summary["period"] == "M"
    assert len(summary["periods"]) == 24
    assert summary["periods"][0] == ("2022-07", 6, True)
    assert summary["periods"][-1] == ("2024-06", 29, True)


def test_two_years_of_complete_months_add_the_last_year_against_the_one_before():
    rows = [(d, 100 if i < 12 else 150) for i, d in enumerate(_months(24))]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert summary["year_over_year"] == ("2022-12", "2023-12", 100, 150, 50, pytest.approx(50))


def test_less_than_two_years_has_no_year_comparison():
    rows = [(d, 100) for d in _months(23)]

    assert temporal_summary(_frame(rows), PROFILE)["year_over_year"] is None


def test_weekly_data_is_averaged_per_month():
    # Mondays from 2024-01-01 to 2024-03-18. January is complete (the week before falls in
    # December); March is not, because the next week (the 25th) would still be in March.
    rows = [(date(2024, 1, 1) + timedelta(weeks=i), 10 * (i // 4 + 1)) for i in range(12)]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert [(label, complete) for label, _, complete in summary["periods"]] == [
        ("2024-01", True), ("2024-02", True), ("2024-03", False),
    ]


def test_quarterly_data_keeps_quarters():
    rows = [(date(2022 + i // 4, 1 + 3 * (i % 4), 1), i) for i in range(8)]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert summary["period"] == "Q"
    assert [label for label, _, _ in summary["periods"]][:2] == ["2022Q1", "2022Q2"]
    assert summary["year_over_year"] == (
        "2022Q4", "2023Q4", 1.5, 5.5, 4, pytest.approx(266.67, 0.01)
    )


@pytest.mark.parametrize(
    "profile",
    [
        {**PROFILE, "date_column_candidate": None},
        {**PROFILE, "columns": [{"name": "ventas", "type": "numeric", "is_identifier": True}]},
    ],
    ids=["no-date-column", "no-forecast-target"],
)
def test_no_summary_without_a_date_column_or_a_target(profile):
    rows = [(d, 1) for d in _days(date(2024, 1, 1), date(2024, 2, 29))]

    assert temporal_summary(_frame(rows), profile) is None


def test_no_summary_for_irregular_dates():
    rows = [(date(2024, 1, 1) + timedelta(days=3 * i), i) for i in range(30)]

    assert temporal_summary(_frame(rows), PROFILE) is None


def test_a_month_missing_only_its_first_day_is_incomplete():
    rows = [(d, 1) for d in _days(date(2024, 1, 2), date(2024, 3, 31))]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert [complete for _, _, complete in summary["periods"]] == [False, True, True]


def test_the_trend_percentage_is_relative_to_the_size_of_a_negative_start():
    rows = [(d, -10 if d.month == 2 else -5) for d in _days(date(2024, 2, 1), date(2024, 3, 31))]

    trend = temporal_summary(_frame(rows), PROFILE)["trend"]

    assert (trend.start, trend.end, trend.change) == (-10, -5, 5)
    assert trend.pct == pytest.approx(50)


@pytest.mark.parametrize(
    ("value", "base", "pct"),
    [(150, 100, 50), (50, 100, -50), (-5, -10, 50), (-15, -10, -50), (5, 0, None)],
)
def test_pct_change_is_relative_to_the_size_of_the_base(value, base, pct):
    result = pct_change(value, base)

    assert result == (pytest.approx(pct) if pct is not None else None)
