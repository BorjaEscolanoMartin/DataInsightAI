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
