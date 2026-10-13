import logging

from app.services.insights_check import check_insights

DATA = """<datos>
Dataset: 730 filas × 6 columnas
  Ventas: media 2.307,52; máximo 8.734,60
  Valores más altos: 2025-11-28 (8.734,60)
  Ventas por grupo: Sí: n = 50, media 2.907,93 (+26,0 %); No: n = 680, media 2.263,10 (-1,9 %)
  2024-10: 1.979,24
  Ventas ↔ Pedidos: r = 0,92 (muy fuerte)
</datos>"""


def _item(title: str, description: str) -> dict:
    return {"title": title, "description": description, "columns": ["Ventas"]}


def _insights(**categories: list[dict]) -> dict:
    return {"trends": [], "anomalies": [], "correlations": [], "recommendations": [], **categories}


def test_insights_whose_figures_are_in_the_data_are_kept():
    kept = _item(
        "Pico de 8.734,60 el 2025-11-28",
        # Exact, rounded (2.308, 8.735), absolute (1,9 % below), dates and periods of the data,
        # and small counts written as words.
        "Las ventas medias son 2.307,52 (unas 2.308) y el máximo, 8.735, en 2025-11-28. "
        "Sin promoción quedan un 1,9 % por debajo; en 2024-10 la media fue 1.979,24. "
        "Hay 3 días destacados y r = 0,92.",
    )

    result, dropped = check_insights(_insights(trends=[kept]), DATA)

    assert result["trends"] == [kept]
    assert dropped == []


def test_an_insight_with_a_figure_not_in_the_data_is_dropped_and_logged(caplog):
    good = _item("Promoción", "Con promoción la media sube a 2.907,93 (+26,0 %).")
    bad = _item("Promoción", "Con promoción se vende un 28,5 % más, 645 al día.")

    with caplog.at_level(logging.WARNING, logger="app.services.insights_check"):
        result, dropped = check_insights(_insights(correlations=[good, bad]), DATA)

    assert result["correlations"] == [good]
    assert [(d.category, d.title, d.missing) for d in dropped] == [
        ("correlations", "Promoción", ["28,5", "645"]),
    ]
    assert caplog.messages == [
        "Insight dropped (correlations, 'Promoción'): figures not in the data: 28,5, 645",
    ]


def test_figures_in_the_title_are_checked_too():
    result, dropped = check_insights(_insights(anomalies=[_item("Triple de 3.000", "Sin cifras.")]),
                                     DATA)

    assert result["anomalies"] == []
    assert dropped[0].missing == ["3.000"]


def test_numbers_in_another_format_are_not_found():
    result, dropped = check_insights(_insights(correlations=[_item("r", "r = 0.92")]), DATA)

    assert result["correlations"] == []
    assert dropped[0].missing == ["0.92"]


def test_a_date_that_is_not_in_the_data_is_checked_as_numbers():
    result, dropped = check_insights(_insights(trends=[_item("Fecha", "El 2023-05-01.")]), DATA)

    assert result["trends"] == []
    assert dropped[0].missing == ["2023"]


def test_counts_above_ten_are_checked():
    result, dropped = check_insights(_insights(trends=[_item("Días", "Hay 11 días.")]), DATA)

    assert dropped[0].missing == ["11"]


def test_when_every_insight_is_dropped_the_result_is_empty():
    insights = _insights(
        trends=[_item("Uno", "Sube un 99 %.")], recommendations=[_item("Dos", "Hasta 12.000.")],
    )

    result, dropped = check_insights(insights, DATA)

    assert result == _insights()
    assert len(dropped) == 2


def test_the_numbers_inside_dates_and_periods_of_the_data_are_not_figures():
    insight = _item("Unidades", "Se vendieron 2024 unidades y 2025 pedidos.")

    result, dropped = check_insights(_insights(trends=[insight]), DATA)

    assert dropped[0].missing == ["2024", "2025"]


def test_an_explicit_sign_must_match_the_data():
    kept = _item("Promoción", "Con promoción +26,0 %, sin ella -1,9 %, entre 2.263-2.908.")
    plus_for_minus = _item("Sin promoción", "Sin promoción las ventas suben un +1,9 %.")
    minus_for_plus = _item("Con promoción", "Con promoción caen un -26,0 %.")

    result, dropped = check_insights(
        _insights(trends=[kept, plus_for_minus, minus_for_plus]), DATA,
    )

    assert result["trends"] == [kept]
    assert [d.missing for d in dropped] == [["+1,9"], ["-26,0"]]
