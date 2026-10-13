import pytest

from app.services.numbers import (
    SPANISH_DATE,
    find_numbers,
    format_day_es,
    format_es,
    format_period_es,
    parse_es,
)


@pytest.mark.parametrize(
    ("value", "decimals", "text"),
    [
        (2908, 0, "2.908"),
        (8734.6, 2, "8.734,60"),
        (0.92, 2, "0,92"),
        (999, 0, "999"),
        (28.456, 1, "28,5"),
        (-1234567.891, 1, "-1.234.567,9"),
        (-0.004, 2, "0"),
        # Whole numbers, once rounded, have no decimals.
        (111, 2, "111"),
        (111.004, 2, "111"),
        (2000.0, 1, "2.000"),
        (25.0, 1, "25"),
    ],
)
def test_format_es_uses_thousands_points_and_a_decimal_comma(value, decimals, text):
    assert format_es(value, decimals) == text


@pytest.mark.parametrize(
    ("text", "value"),
    [("2.908", 2908), ("8.734,60", 8734.6), ("0,92", 0.92), ("-1.234.567,9", -1234567.9)],
)
def test_parse_es_reads_what_format_es_writes(text, value):
    assert parse_es(text) == pytest.approx(value)


@pytest.mark.parametrize("text", ["0.92", "1,234.56", "1.23", "12.3456", ",5", ""])
def test_parse_es_rejects_other_formats(text):
    with pytest.raises(ValueError):
        parse_es(text)


@pytest.mark.parametrize(
    "value", [0, 7, 111, 0.5, 0.92, 28.456, 999.5, 1000, 2907.93, 8734.6, -1234567.891, 1e9 + 0.25]
)
@pytest.mark.parametrize("decimals", [0, 1, 2, 3])
def test_parse_es_undoes_format_es(value, decimals):
    assert parse_es(format_es(value, decimals)) == pytest.approx(round(value, decimals))


@pytest.mark.parametrize("decimals", [0, 1, 2])
def test_find_numbers_reads_every_number_format_es_writes(decimals):
    values = [2907.93, -0.36, 28.456, 1234567.891]
    text = "Medias: " + "; ".join(format_es(v, decimals) for v in values) + "."

    found = find_numbers(text)

    assert [n.value for n in found] == pytest.approx([round(v, decimals) for v in values])
    assert [n.decimals for n in found] == [decimals] * len(values)


def test_find_numbers_keeps_numbers_in_other_formats_as_unreadable():
    found = find_numbers("Con promoción 2.908 (+28,5 %), r=0.92 y 1,234.56 en total.")

    assert [(n.text, n.value, n.decimals) for n in found] == [
        ("2.908", 2908, 0),
        ("+28,5", 28.5, 1),
        ("0.92", None, 0),
        ("1,234.56", None, 0),
    ]


def test_find_numbers_reads_numbers_glued_to_letters():
    found = find_numbers("En Q3, a las 12h, 2.908€ y 28%.")

    assert [n.value for n in found] == [3, 12, 2908, 28]


def test_find_numbers_tells_an_explicit_sign_from_a_hyphen_between_numbers():
    found = find_numbers("Sube (+28,5 %) o baja -1,9 %; rango 163-239 en 2024-2025.")

    assert [(n.text, n.value, n.sign) for n in found] == [
        ("+28,5", 28.5, "+"),
        ("-1,9", -1.9, "-"),
        ("163", 163, ""),
        ("239", 239, ""),
        ("2024", 2024, ""),
        ("2025", 2025, ""),
    ]


@pytest.mark.parametrize(
    ("iso", "text"),
    [("2025-11-28", "28 nov 2025"), ("2024-01-05", "5 ene 2024"), ("2026-09-30", "30 sep 2026")],
)
def test_format_day_es_writes_day_month_and_year(iso, text):
    assert format_day_es(iso) == text


@pytest.mark.parametrize(
    ("label", "text"),
    [("2024-10", "oct 2024"), ("2025-05", "may 2025"), ("2024Q1", "T1 2024"), ("2024", "2024")],
)
def test_format_period_es_writes_months_quarters_and_years(label, text):
    assert format_period_es(label) == text


def test_spanish_date_matches_what_the_formatters_write():
    text = "Del 28 nov 2025 a oct 2024, en T3 2023 y 5 ene 2024."

    assert SPANISH_DATE.findall(text) == ["28 nov 2025", "oct 2024", "T3 2023", "5 ene 2024"]
