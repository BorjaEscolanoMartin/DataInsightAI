from datetime import date, timedelta

import pandas as pd
import pytest

from app.services.data_summary import breakdowns
from app.services.profiling import profile_csv


def _summarise(df: pd.DataFrame) -> dict | None:
    profile = profile_csv(df.to_csv(index=False).encode())
    return breakdowns(df, profile)


def _dates(count: int) -> list[str]:
    return [str(date(2024, 1, 1) + timedelta(days=i)) for i in range(count)]


def test_target_mean_per_group_with_n_and_percentage_against_the_overall_mean():
    df = pd.DataFrame({
        "fecha": _dates(8),
        "ventas": [30, 50] + [10] * 6,
        "promo": ["No", "No"] + ["Sí"] * 6,
        # An identifier with few values is still not a group.
        "fila": range(1, 9),
    })

    result = _summarise(df)

    assert result["target"] == "ventas"
    assert result["overall_mean"] == pytest.approx(17.5)
    [promo] = result["columns"]
    assert promo.column == "promo"
    # Largest groups first, not in alphabetical order.
    assert [(g.label, g.n, g.mean) for g in promo.groups] == [("Sí", 6, 10), ("No", 2, 40)]
    assert [g.pct for g in promo.groups] == pytest.approx([-42.857, 128.571], abs=0.001)


def _housing(rows: int = 40) -> pd.DataFrame:
    return pd.DataFrame({
        "id": range(1, rows + 1),
        "zona": ["Playa" if i % 4 == 0 else "Centro" for i in range(rows)],
        "baños": [1 + i % 4 for i in range(rows)],
        "metros": [50 + 3 * i for i in range(rows)],
        "precio": [100 + 10 * (i % 4) + (500 if i % 4 == 0 else 0) for i in range(rows)],
    })


def test_without_a_date_the_target_is_the_regression_target():
    assert _summarise(_housing())["target"] == "precio"


def test_low_cardinality_numeric_columns_are_grouped_and_identifiers_are_not():
    columns = [c.column for c in _summarise(_housing())["columns"]]

    # baños has 4 values; metros has 40 and id is an identifier; precio is the target.
    assert sorted(columns) == ["baños", "zona"]


def test_columns_with_the_widest_spread_of_means_come_first_and_at_most_four():
    rows = 60
    # precio is 0..59; spread (widest group mean minus narrowest): a 30, otra 3, d 2.5, c 1.5,
    # b 1, e 0.5.
    df = pd.DataFrame({
        "a": ["x" if i < 30 else "y" for i in range(rows)],
        "b": ["x" if i % 2 else "y" for i in range(rows)],
        "c": ["x" if i % 3 else "y" for i in range(rows)],
        "d": ["x" if i % 5 else "y" for i in range(rows)],
        "e": ["x" if i != 30 else "y" for i in range(rows)],
        "otra": [float(i % 7) for i in range(rows)],
        "precio": [float(i) for i in range(rows)],
    })

    result = _summarise(df)

    assert [c.column for c in result["columns"]] == ["a", "otra", "d", "c"]


def test_more_than_ten_groups_keep_the_ten_largest_and_join_the_rest():
    labels = [f"g{k:02d}" for k in range(12) for _ in range(12 - k)]
    df = pd.DataFrame({
        "metros": [float(i) for i in range(len(labels))],
        "precio": [float(k) for k in range(12) for _ in range(12 - k)],
        "grupo": labels,
    })

    [grupo] = _summarise(df)["columns"]

    assert [g.label for g in grupo.groups] == [f"g{k:02d}" for k in range(10)] + ["otros"]
    # g10 (2 rows of 10) and g11 (1 row of 11).
    assert (grupo.groups[-1].n, grupo.groups[-1].mean) == (3, pytest.approx(31 / 3))


def test_outliers_are_split_into_low_and_high_sides_with_their_ranges():
    values = [50.0] * 20 + [51.0] * 20 + [1.0, 2.0, 200.0, 250.0, 300.0]
    df = pd.DataFrame({"metros": values, "precio": [2.0 * v for v in range(len(values))]})

    outliers = {o.column: o for o in _summarise(df)["outliers"]}

    assert (outliers["metros"].low.n, outliers["metros"].low.min, outliers["metros"].low.max) == (
        2, 1, 2,
    )
    assert (outliers["metros"].high.n, outliers["metros"].high.min,
            outliers["metros"].high.max) == (3, 200, 300)
    # precio is spread evenly: no outliers, so no entry.
    assert "precio" not in outliers


def test_the_target_outliers_are_described_by_their_most_common_groups():
    df = _housing(80)

    result = _summarise(df)

    # Price outliers are the Playa homes with 1 bathroom (every fourth row).
    by_column = {c: groups for c, groups in result["target_outliers"]}
    assert by_column["zona"] == [("Playa", 20)]
    assert by_column["baños"] == [("1", 20)]


def test_the_target_outliers_keep_their_three_most_common_groups():
    zones = ["z1"] * 4 + ["z2"] * 3 + ["z3"] * 2 + ["z4"]
    df = pd.DataFrame({
        "metros": [float(i) for i in range(50)],
        "zona": ["base"] * 40 + zones,
        "precio": [100.0 + i % 5 for i in range(40)] + [1000.0] * 10,
    })

    by_column = dict(_summarise(df)["target_outliers"])

    assert by_column["zona"] == [("z1", 4), ("z2", 3), ("z3", 2)]


def test_no_breakdown_without_a_target():
    df = pd.DataFrame({"zona": ["a", "b"] * 5, "nombre": [f"n{i}" for i in range(10)]})

    assert _summarise(df) is None
