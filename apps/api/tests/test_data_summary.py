from datetime import date, timedelta

import pandas as pd
import pytest

from app.services.data_summary import pct_change, summary_target, temporal_summary

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


def _years(summary: dict) -> list[tuple]:
    return [
        (y.year, y.covered, y.first, y.last, y.missing, y.complete_count,
         [p.label for p in y.highest], y.highest[0].mean if y.highest else None,
         [p.label for p in y.lowest], y.lowest[0].mean if y.lowest else None)
        for y in summary["years"]
    ]


def _monthly(values: dict[date, float]) -> pd.DataFrame:
    return _frame(sorted(values.items()))


def test_each_calendar_year_gets_its_highest_and_lowest_month_and_the_months_it_spans():
    # Oct 2024 to Sep 2026, every month complete; each month's value is unique.
    days = _days(date(2024, 10, 1), date(2026, 9, 30))
    rows = [(d, (d.year - 2024) * 100 + d.month) for d in days]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert _years(summary) == [
        ("2024", False, "2024-10", "2024-12", [], 3, ["2024-12"], 12, ["2024-10"], 10),
        ("2025", True, "2025-01", "2025-12", [], 12, ["2025-12"], 112, ["2025-01"], 101),
        ("2026", False, "2026-01", "2026-09", [], 9, ["2026-09"], 209, ["2026-01"], 201),
    ]


def test_a_partial_month_is_never_a_year_extreme_nor_part_of_its_span():
    # January starts on the 15th and April ends on the 10th: both are partial.
    values = {1: 90, 2: 20, 3: 30, 4: 5}
    rows = [(d, values[d.month]) for d in _days(date(2024, 1, 15), date(2024, 4, 10))]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert _years(summary) == [
        ("2024", False, "2024-02", "2024-03", [], 2, ["2024-03"], 30, ["2024-02"], 20),
    ]


def test_a_year_with_fewer_than_two_complete_months_is_listed_without_extremes():
    # 10 Dec 2024 to 31 Jan 2025 then up to 10 Feb: 2024 has no complete month, 2025 one.
    rows = [(d, d.month) for d in _days(date(2024, 12, 10), date(2025, 2, 10))]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert _years(summary) == [
        ("2024", False, None, None, [], 0, [], None, [], None),
        ("2025", False, "2025-01", "2025-01", [], 1, [], None, [], None),
    ]


def test_months_missing_inside_a_year_are_listed():
    values = {date(2025, m, 1): 10 * m for m in range(1, 13) if m not in (3, 4)}

    summary = temporal_summary(_monthly(values), PROFILE)

    assert _years(summary) == [
        ("2025", False, "2025-01", "2025-12", ["2025-03", "2025-04"], 10,
         ["2025-12"], 120, ["2025-01"], 10),
    ]


def test_every_tied_month_is_named():
    values = {date(2025, m, 1): 10 + m for m in range(1, 13)}
    values[date(2025, 11, 1)] = values[date(2025, 12, 1)] = 50
    values[date(2025, 6, 1)] = values[date(2025, 1, 1)] = 1

    summary = temporal_summary(_monthly(values), PROFILE)

    assert _years(summary) == [
        ("2025", True, "2025-01", "2025-12", [], 12,
         ["2025-11", "2025-12"], 50, ["2025-01", "2025-06"], 1),
    ]


def test_quarters_are_grouped_by_year_too():
    quarters = [date(2023, m, 1) for m in (1, 4, 7, 10)] + [date(2024, 1, 1), date(2024, 4, 1)]
    rows = list(zip(quarters, [40, 10, 30, 20, 50, 60], strict=True))

    summary = temporal_summary(_frame(rows), PROFILE)

    assert summary["period"] == "Q"
    assert _years(summary) == [
        ("2023", True, "2023Q1", "2023Q4", [], 4, ["2023Q1"], 40, ["2023Q2"], 10),
        ("2024", False, "2024Q1", "2024Q2", [], 2, ["2024Q2"], 60, ["2024Q1"], 50),
    ]


def test_yearly_data_has_no_extremes_within_a_year():
    rows = [(date(y, 1, 1), y - 2000) for y in range(2015, 2025)]

    summary = temporal_summary(_frame(rows), PROFILE)

    assert summary["period"] == "Y"
    assert summary["years"] == []


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


def test_without_a_date_the_summary_target_skips_a_final_identifier():
    profile = {
        "date_column_candidate": None,
        "columns": [
            {"name": "metros", "type": "numeric", "is_identifier": False},
            {"name": "precio", "type": "numeric", "is_identifier": False},
            {"name": "id", "type": "numeric", "is_identifier": True},
        ],
    }

    assert summary_target(profile) == "precio"
