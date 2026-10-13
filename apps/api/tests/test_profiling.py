import textwrap

import pytest

from app.services.profiling import profile_csv

CSV_NUMERIC = textwrap.dedent("""\
    fecha,ventas,categoria,activo
    2024-01-01,100,A,true
    2024-01-02,200,B,false
    2024-01-03,150,A,true
    2024-01-04,300,C,false
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


def test_histogram_keeps_empty_bins_between_distant_values():
    csv = b"valor,nombre\n1,a\n1,b\n1,c\n21,d\n21,e\n"
    result = profile_csv(csv)
    hist = next(c for c in result["charts"] if c["id"] == "hist_valor")

    assert [b["count"] for b in hist["data"]] == [3] + [0] * 18 + [2]
    assert hist["data"][0]["bin"] == "1–2"
    assert hist["data"][1]["bin"] == "2–3"
    assert hist["data"][-1]["bin"] == "20–21"


CSV_IDENTIFIERS = textwrap.dedent("""\
    fila,cliente_id,ID cliente,Id. de la fila,Pedidos,Paid,pedido_id,medida,precio,categoria
    3,10,10,10,10,10,7,1.5,1.5,a
    1,,40,40,40,40,7,2.5,2,b
    5,25,25,25,25,25,8,3.5,3,c
    2,7,7,7,7,7,9,4.5,4,d
    4,99,99,99,99,99,10,5.5,5,e
""").encode()


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
        # Same values, but "id" is only part of a word.
        "Pedidos": False,
        "Paid": False,
        # Repeated or non-integer values are never identifiers, whatever the name or span.
        "pedido_id": False,
        "medida": False,
        "precio": False,
        "categoria": False,
    }
