import textwrap

import numpy as np
import pandas as pd
import pytest

from app.services.profiling import iqr_bounds, profile_csv, read_csv

CSV_NUMERIC = textwrap.dedent("""\
    fecha,ventas,categoria,activo
    2024-01-01,100,A,true
    2024-01-02,200,B,false
    2024-01-03,150,A,true
    2024-01-04,300.5,C,false
    2024-01-05,250,B,true
    2024-01-06,180,A,false
    2024-01-07,220,C,true
    2024-01-08,90,B,false
    2024-01-09,310,A,true
    2024-01-10,170,C,false
""").encode()


def test_basic_shape():
    result = profile_csv(CSV_NUMERIC)
    assert result["row_count"] == 10
    assert result["column_count"] == 4


def test_column_types():
    result = profile_csv(CSV_NUMERIC)
    types = {c["name"]: c["type"] for c in result["columns"]}
    assert types["ventas"] == "numeric"
    assert types["categoria"] == "categorical"
    assert types["fecha"] == "date"


def test_numeric_stats():
    result = profile_csv(CSV_NUMERIC)
    ventas = next(c for c in result["columns"] if c["name"] == "ventas")
    assert ventas["mean"] == pytest.approx(197.0, rel=0.01)
    assert ventas["min_val"] == 90.0
    assert ventas["max_val"] == 310.0
    assert ventas["null_count"] == 0
    assert ventas["null_pct"] == 0.0


def test_categorical_top_categories():
    result = profile_csv(CSV_NUMERIC)
    categoria = next(c for c in result["columns"] if c["name"] == "categoria")
    assert "top_categories" in categoria
    assert len(categoria["top_categories"]) > 0
    values = [c["value"] for c in categoria["top_categories"]]
    assert "A" in values


def test_date_candidate_detected():
    result = profile_csv(CSV_NUMERIC)
    assert result["date_column_candidate"] == "fecha"


def test_charts_generated():
    result = profile_csv(CSV_NUMERIC)
    chart_types = {c["type"] for c in result["charts"]}
    assert "histogram" in chart_types
    assert "bar" in chart_types
    assert "line" in chart_types


def test_null_percentage():
    csv = b"a,b\n1,\n2,2\n3,\n"
    result = profile_csv(csv)
    col_b = next(c for c in result["columns"] if c["name"] == "b")
    assert col_b["null_count"] == 2
    assert col_b["null_pct"] == pytest.approx(66.67, rel=0.01)


def test_handles_latin1_encoding():
    csv = "nombre,valor\nJosé,10\nMaría,20\n".encode("latin-1")
    result = profile_csv(csv)
    assert result["row_count"] == 2


def _histogram(values: list[float]) -> list[dict]:
    # A second column keeps the delimiter sniffer from taking the decimal point.
    csv = "valor,nombre\n" + "".join(f"{v},x\n" for v in values)
    result = profile_csv(csv.encode())
    return next(c for c in result["charts"] if c["id"] == "hist_valor")["data"]


def test_histogram_keeps_empty_bins_between_distant_values():
    # Decimal values: whole numbers with few distinct values are drawn as bars instead.
    bins = _histogram([1, 1.2, 1.5, 20.5, 21])

    assert [b["count"] for b in bins] == [3] + [0] * 18 + [2]
    assert bins[0] == {"bin": "1–2", "start": 1.0, "end": 2.0, "count": 3}
    assert bins[1]["bin"] == "2–3"
    assert bins[-1] == {"bin": "20–21", "start": 20.0, "end": 21.0, "count": 2}


def test_histogram_bins_cover_the_iqr_range_and_group_the_extremes():
    # Quartiles 4.75 and 15.25: the IQR bounds are -11 and 31.
    bins = _histogram([-1000.5] + [i + 0.5 for i in range(20)] + [1000.5])

    assert len(bins) == 22
    assert bins[0] == {"bin": "< -11", "start": None, "end": -11.0, "count": 1}
    assert bins[1]["start"] == -11.0
    assert bins[1]["end"] == pytest.approx(-8.9)
    assert bins[20]["end"] == 31.0
    assert sum(b["count"] for b in bins[1:21]) == 20
    assert bins[-1] == {"bin": "> 31", "start": 31.0, "end": None, "count": 1}


def test_histogram_without_values_below_has_no_lower_extreme_bin():
    # Quartiles 5.5 and 15.5: the bounds are -9.5 and 30.5; the range starts at the minimum.
    bins = _histogram([i + 0.5 for i in range(20)] + [1000.5])

    assert len(bins) == 21
    assert bins[0]["start"] == 0.5
    assert bins[-1] == {"bin": "> 30.5", "start": 30.5, "end": None, "count": 1}


def test_histogram_with_zero_iqr_uses_the_full_range():
    bins = _histogram([1.5] * 10 + [2.5, 9.5])

    assert len(bins) == 20
    assert bins[0]["start"] == 1.5
    assert bins[-1]["end"] == 9.5
    assert all(b["start"] is not None and b["end"] is not None for b in bins)
    assert sum(b["count"] for b in bins) == 12


def _charts(values: list[str]) -> dict[str, dict]:
    csv = "valor,nombre\n" + "".join(f"{v},x\n" for v in values)
    return {c["id"]: c for c in profile_csv(csv.encode())["charts"]}


def test_whole_numbers_with_few_values_are_bars_of_each_value():
    # Ten distinct values, unordered, and an empty cell (read as a float column).
    charts = _charts(["3", "1", "3", "", "10", "2", "4", "5", "6", "7", "8", "9", "3"])

    assert "hist_valor" not in charts
    bar = charts["bar_valor"]
    assert (bar["type"], bar["title"], bar["column"]) == ("bar", "Distribución de valor", "valor")
    assert bar["data"][:3] == [
        {"name": "1", "value": 1, "count": 1},
        {"name": "2", "value": 2, "count": 1},
        {"name": "3", "value": 3, "count": 3},
    ]
    assert [b["value"] for b in bar["data"]] == list(range(1, 11))
    assert all(isinstance(b["value"], int) for b in bar["data"])


def test_whole_numbers_with_more_values_stay_a_histogram():
    charts = _charts([str(v) for v in range(11)])

    assert "bar_valor" not in charts
    assert charts["hist_valor"]["type"] == "histogram"


def test_decimal_numbers_with_few_values_stay_a_histogram():
    charts = _charts(["1.5", "2.5", "1.5", "3.5"])

    assert "bar_valor" not in charts
    assert charts["hist_valor"]["type"] == "histogram"


CSV_IDENTIFIERS = (
    "fila,cliente_id,ID cliente,Id. de la fila,CustomerId,customerId,"
    "Pedidos,Paid,pedido_id,medida,precio,categoria\n"
    + textwrap.dedent("""\
    3,10,10,10,10,10,10,10,7,1.5,1.5,a
    1,,40,40,40,40,40,40,7,2.5,2,b
    5,25,25,25,25,25,25,25,8,3.5,3,c
    2,7,7,7,7,7,7,7,9,4.5,4,d
    4,99,99,99,99,99,99,99,10,5.5,5,e
""")
).encode()


def test_identifier_columns_are_flagged():
    result = profile_csv(CSV_IDENTIFIERS)
    flags = {c["name"]: c["is_identifier"] for c in result["columns"]}

    assert flags == {
        # A consecutive range of distinct integers, in any order.
        "fila": True,
        # Distinct integers whose name has the token "id"; nulls are ignored.
        "cliente_id": True,
        "ID cliente": True,
        "Id. de la fila": True,
        # A change from lower to upper case also splits the name.
        "CustomerId": True,
        "customerId": True,
        # Same values, but "id" is only part of a word.
        "Pedidos": False,
        "Paid": False,
        # Repeated or non-integer values are never identifiers, whatever the name or span.
        "pedido_id": False,
        "medida": False,
        "precio": False,
        "categoria": False,
    }


def test_iqr_bounds_are_one_and_a_half_iqr_beyond_the_quartiles():
    low, high = iqr_bounds(pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9]))

    # Q1 = 3, Q3 = 7, IQR = 4.
    assert (low, high) == (-3, 13)


def test_iqr_bounds_are_none_when_the_quartiles_are_equal():
    assert iqr_bounds(pd.Series([5, 5, 5, 5, 9])) is None


def test_read_csv_sniffs_the_delimiter_and_the_encoding():
    df = read_csv("zona;precio\nMálaga;10\nCádiz;20\n".encode("latin-1"))

    assert df.columns.tolist() == ["zona", "precio"]
    assert df["zona"].tolist() == ["Málaga", "Cádiz"]


def test_read_csv_rejects_unreadable_content():
    with pytest.raises(ValueError, match="No se pudo leer el CSV"):
        read_csv(b"")


def _column(result: dict, name: str) -> dict:
    return next(c for c in result["columns"] if c["name"] == name)


def test_date_column_has_its_range_in_iso():
    content = b"fecha,ventas\n2024-03-05,1\n2024-01-02,2\n2024-12-31,3\n2024-02-29,4\n"

    result = profile_csv(content)

    fecha = _column(result, "fecha")
    assert fecha["min_date"] == "2024-01-02"
    assert fecha["max_date"] == "2024-12-31"
    assert "min_date" not in _column(result, "ventas")


def test_a_datetime_column_gives_calendar_dates():
    content = (
        b"momento,valor\n"
        b"2025-06-01 23:59:00,1\n2025-05-30 08:15:00,2\n2025-06-02 00:00:00,3\n"
    )

    result = profile_csv(content)

    momento = _column(result, "momento")
    assert (momento["min_date"], momento["max_date"]) == ("2025-05-30", "2025-06-02")


def test_every_date_column_has_its_own_range():
    content = (
        b"pedido,entrega,importe\n"
        b"2024-01-10,2024/01/15,5\n2024-01-03,2024/01/09,7\n2024-02-01,2024/02/20,9\n"
    )

    result = profile_csv(content)

    assert result["date_column_candidate"] == "pedido"
    assert (_column(result, "pedido")["min_date"], _column(result, "pedido")["max_date"]) == (
        "2024-01-03",
        "2024-02-01",
    )
    assert (_column(result, "entrega")["min_date"], _column(result, "entrega")["max_date"]) == (
        "2024-01-09",
        "2024-02-20",
    )


def test_missing_dates_do_not_count_in_the_range():
    content = b"fecha,ventas\n2024-01-05,1\n,2\n2024-01-01,3\n,4\n2024-01-09,5\n"

    result = profile_csv(content)

    fecha = _column(result, "fecha")
    assert (fecha["min_date"], fecha["max_date"]) == ("2024-01-01", "2024-01-09")


def test_without_a_date_column_no_column_has_a_range():
    content = b"ventas,zona\n1,A\n2,B\n3,A\n"

    result = profile_csv(content)

    assert result["date_column_candidate"] is None
    assert all("min_date" not in c and "max_date" not in c for c in result["columns"])


def test_the_profile_schema_keeps_the_range_and_reads_old_profiles():
    from app.schemas.datasets import DatasetProfileOut

    new = DatasetProfileOut.model_validate(profile_csv(CSV_NUMERIC))
    fecha = next(c for c in new.columns if c.name == "fecha")
    assert (fecha.min_date, fecha.max_date) == ("2024-01-01", "2024-01-10")

    old = profile_csv(CSV_NUMERIC)
    for column in old["columns"]:
        column.pop("min_date", None)
        column.pop("max_date", None)
    legacy = DatasetProfileOut.model_validate(old)
    fecha = next(c for c in legacy.columns if c.name == "fecha")
    assert (fecha.min_date, fecha.max_date) == (None, None)


def test_a_date_column_with_mixed_time_zones_profiles_without_a_range():
    # Typed as a date from its first 50 values, but later rows change the UTC offset: the whole
    # column cannot be read in one go. The profile must not fail; the column just has no range.
    rows = [f"2025-03-{d:02d}T10:00:00+01:00,{d}" for d in range(1, 31)] * 2
    rows += [f"2025-04-{d:02d}T10:00:00+02:00,{d}" for d in range(1, 31)]
    content = ("momento,valor\n" + "\n".join(rows) + "\n").encode()

    result = profile_csv(content)

    momento = _column(result, "momento")
    assert momento["type"] == "date"
    assert "min_date" not in momento and "max_date" not in momento
    assert _column(result, "valor")["max_val"] == 30


def test_scatter_pairs_leave_out_discrete_columns():
    # habitaciones (1-10) correlates with metros almost as much as precio does.
    rows = [(i + 0.5, 2 * i + 1.25 + (i % 3) * 0.1, i // 3 + 1) for i in range(30)]
    csv = "metros,precio,habitaciones\n" + "".join(f"{m},{p},{h}\n" for m, p, h in rows)
    charts = profile_csv(csv.encode())["charts"]

    scatters = [(c["x_column"], c["y_column"]) for c in charts if c["type"] == "scatter"]
    assert scatters == [("metros", "precio")]


def test_scatter_finds_a_continuous_pair_beyond_the_heatmap_columns():
    # Nine discrete columns first: the correlated pair is the 15th and 16th numeric columns,
    # and the heatmap's correlations only cover the first 15.
    rng = np.random.default_rng(0)
    df = pd.DataFrame({f"d{i}": rng.integers(1, 5, 50) for i in range(9)})
    for i in range(6):
        df[f"c{i}"] = rng.normal(size=50).round(3)
    df["c6"] = (df["c5"] + rng.normal(scale=0.1, size=50)).round(3)
    charts = profile_csv(df.to_csv(index=False).encode())["charts"]

    scatters = [(c["x_column"], c["y_column"]) for c in charts if c["type"] == "scatter"]
    assert scatters == [("c5", "c6")]


def _bar_ids(counts: dict[str, int]) -> set[str]:
    values = [name for name, n in counts.items() for _ in range(n)]
    # A second, uneven column keeps its chart, so the CSV still has bar charts.
    otros = ["a"] * (len(values) - 1) + ["b"]
    csv = "categoria,otro\n" + "".join(f"{v},{o}\n" for v, o in zip(values, otros, strict=True))
    return {c["id"] for c in profile_csv(csv.encode())["charts"] if c["type"] == "bar"}


def test_nearly_uniform_categories_get_no_chart():
    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    ids = _bar_ids({d: 105 if d in ("Martes", "Miércoles") else 104 for d in days})

    assert ids == {"bar_otro"}


def test_uniformity_bound_is_one_point_one():
    assert _bar_ids({"x": 11, "y": 10}) == {"bar_otro"}
    assert _bar_ids({"x": 12, "y": 10}) == {"bar_categoria", "bar_otro"}


def test_uniformity_counts_every_category_not_only_the_top_ten():
    # The ten most frequent are even; the eleventh, outside the profile's top 10, is not.
    counts = {f"c{i:02d}": 5 for i in range(10)} | {"c10": 1}

    assert _bar_ids(counts) == {"bar_categoria", "bar_otro"}
