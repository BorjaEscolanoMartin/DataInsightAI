import pytest

from app.services.numbers import find_numbers, format_es, parse_es


@pytest.mark.parametrize(
    ("value", "decimals", "text"),
    [
        (2908, 0, "2.908"),
        (8734.6, 2, "8.734,60"),
        (0.92, 2, "0,92"),
        (999, 0, "999"),
        (28.456, 1, "28,5"),
        (-1234567.891, 1, "-1.234.567,9"),
        (-0.004, 2, "0,00"),
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
    "value", [0, 7, 0.5, 0.92, 28.456, 999.5, 1000, 2907.93, 8734.6, -1234567.891, 1e9 + 0.25]
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
        ("28,5", 28.5, 1),
        ("0.92", None, 0),
        ("1,234.56", None, 0),
    ]


def test_find_numbers_reads_numbers_glued_to_letters():
    found = find_numbers("En Q3, a las 12h, 2.908€ y 28%.")

    assert [n.value for n in found] == [3, 12, 2908, 28]
