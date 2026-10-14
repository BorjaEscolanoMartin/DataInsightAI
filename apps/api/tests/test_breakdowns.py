import logging
from datetime import date, timedelta

import pandas as pd
import pytest

from app.services import data_summary
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
        "id_fila": range(1, 9),
    })

    result = _summarise(df)

    assert result["target"] == "ventas"
    assert result["overall_mean"] == pytest.approx(17.5)
    [promo] = result["columns"]
    assert promo.column == "promo"
    # Largest groups first, not in alphabetical order.
    assert [(g.label, g.n, g.mean) for g in promo.groups] == [("Sí", 6, 10), ("No", 2, 40)]
    assert [g.pct for g in promo.groups] == pytest.approx([-42.857, 128.571], abs=0.001)
    # Two groups: the smaller one against the larger one.
    assert promo.difference == ("No", "Sí", 30, pytest.approx(300))


def _housing(rows: int = 40) -> pd.DataFrame:
    return pd.DataFrame({
        "id": range(1, rows + 1),
        "zona": ["Playa" if i % 4 == 0 else "Centro" for i in range(rows)],
        "baños": [1 + i % 4 for i in range(rows)],
        "metros": [50 + 3 * i for i in range(rows)],
        "precio": [100 + 10 * (i % 4) + (500 if i % 4 == 0 else 0) for i in range(rows)],
    })


def test_columns_with_more_than_two_groups_have_no_difference():
    columns = {c.column: c for c in _summarise(_housing())["columns"]}

    assert columns["baños"].difference is None
    assert columns["zona"].difference is not None


def test_without_a_date_the_target_is_the_regression_target():
    assert _summarise(_housing())["target"] == "precio"


def test_low_cardinality_numeric_columns_are_grouped_and_identifiers_are_not():
    columns = [c.column for c in _summarise(_housing())["columns"]]

    # baños has 4 values; metros has 40 and id is an identifier; precio is the target.
    assert sorted(columns) == ["baños", "zona"]


def test_columns_with_the_widest_spread_of_means_come_first_and_at_most_four():
    rows = 60
    # precio is 0.5..59.5 (a counter of whole numbers would be an identifier); spread (widest
    # group mean minus narrowest): a 30, otra 3, d 2.5, c 1.5, b 1, e 0.5.
    df = pd.DataFrame({
        "a": ["x" if i < 30 else "y" for i in range(rows)],
        "b": ["x" if i % 2 else "y" for i in range(rows)],
        "c": ["x" if i % 3 else "y" for i in range(rows)],
        "d": ["x" if i % 5 else "y" for i in range(rows)],
        "e": ["x" if i != 30 else "y" for i in range(rows)],
        "otra": [float(i % 7) for i in range(rows)],
        "precio": [i + 0.5 for i in range(rows)],
    })

    result = _summarise(df)

    assert [c.column for c in result["columns"]] == ["a", "otra", "d", "c"]


def test_more_than_ten_groups_keep_the_ten_largest_and_join_the_rest():
    labels = [f"g{k:02d}" for k in range(12) for _ in range(12 - k)]
    df = pd.DataFrame({
        # Decimals: whole numbers rising by one would be a row counter, not a feature.
        "metros": [i + 0.5 for i in range(len(labels))],
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
        # Decimals: whole numbers rising by one would be a row counter, not a feature.
        "metros": [i + 0.5 for i in range(50)],
        "zona": ["base"] * 40 + zones,
        "precio": [100.0 + i % 5 for i in range(40)] + [1000.0] * 10,
    })

    by_column = dict(_summarise(df)["target_outliers"])

    assert by_column["zona"] == [("z1", 4), ("z2", 3), ("z3", 2)]


def test_no_breakdown_without_a_target():
    df = pd.DataFrame({"zona": ["a", "b"] * 5, "nombre": [f"n{i}" for i in range(10)]})

    assert _summarise(df) is None


def test_decimal_group_labels_are_written_in_spanish_format():
    df = pd.DataFrame({
        "metros": [float(50 + 7 * i % 97) for i in range(40)],
        "baños": [(1, 1.5, 2, 2.5)[i % 4] for i in range(40)],
        # Whole numbers stored as floats (2019.0) stay plain, never "2.019".
        "año": [float(2019 + i % 4) for i in range(40)],
        "precio": [100.0 + 10 * (i % 4) + i % 3 for i in range(40)],
    })

    columns = {c.column: c for c in _summarise(df)["columns"]}

    assert sorted(g.label for g in columns["baños"].groups) == ["1", "1,5", "2", "2,5"]
    assert sorted(g.label for g in columns["año"].groups) == ["2019", "2020", "2021", "2022"]


def _three_columns(rows: int = 40) -> pd.DataFrame:
    return pd.DataFrame({
        "zona": ["a" if i % 2 else "b" for i in range(rows)],
        "tipo": ["x" if i % 3 else "y" for i in range(rows)],
        "metros": [float(50 + 7 * i % 97) for i in range(rows)],
        "precio": [100.0 + i % 5 + 10 * (i % 2) for i in range(rows)],
    })


def test_a_column_that_fails_is_skipped_and_the_others_are_kept(monkeypatch, caplog):
    real = data_summary._groups

    def groups(df, column, target, overall):
        if column == "zona":
            raise ValueError("boom")
        return real(df, column, target, overall)

    monkeypatch.setattr(data_summary, "_groups", groups)

    with caplog.at_level(logging.WARNING, logger="app.services.data_summary"):
        result = _summarise(_three_columns())

    assert [c.column for c in result["columns"]] == ["tipo"]
    # The column is named by its position, not by its CSV text.
    assert caplog.messages == ["Breakdown skipped column 0: ValueError"]


def test_a_column_whose_outliers_fail_is_skipped_and_the_others_are_kept(monkeypatch, caplog):
    df = _three_columns()
    df["metros"] = [1.0] * 38 + [500.0, 900.0]
    df["precio"] = [100.0] * 30 + [101.0] * 8 + [700.0, 800.0]
    real = data_summary._sides

    def sides(values):
        if values.name == "metros":
            raise ValueError("boom")
        return real(values)

    monkeypatch.setattr(data_summary, "_sides", sides)

    with caplog.at_level(logging.WARNING, logger="app.services.data_summary"):
        result = _summarise(df)

    assert [o.column for o in result["outliers"]] == ["precio"]
    assert caplog.messages == ["Outliers skipped column 2: ValueError"]


def test_a_column_without_rows_shared_with_the_target_is_ignored(caplog):
    df = _three_columns()
    # Before precio, which must stay the last numeric column (the regression target).
    df.insert(2, "vacía", float("nan"))

    with caplog.at_level(logging.WARNING, logger="app.services.data_summary"):
        result = _summarise(df)

    assert sorted(c.column for c in result["columns"]) == ["tipo", "zona"]
    assert caplog.messages == []


def test_tiny_decimal_labels_are_written_in_full():
    df = _three_columns()
    df.insert(2, "tasa", [(1e-05, 2.5e-05, 1.5e-07)[i % 3] for i in range(len(df))])

    columns = {c.column: c for c in _summarise(df)["columns"]}

    assert sorted(g.label for g in columns["tasa"].groups) == [
        "0,00000015", "0,00001", "0,000025",
    ]
