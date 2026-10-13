import uuid

import pytest

from tests.conftest import USER_A, USER_B


def test_analysis_of_another_user_looks_like_a_missing_one(client, as_user, make_dataset):
    _, dataset, analysis = make_dataset(USER_A)
    owner = client.get(f"/api/analyses/{analysis.id}")
    assert owner.status_code == 200
    assert owner.json()["id"] == str(analysis.id)
    assert owner.json()["dataset_id"] == str(dataset.id)

    as_user(USER_B)
    response = client.get(f"/api/analyses/{analysis.id}")
    missing = client.get(f"/api/analyses/{uuid.uuid4()}")

    # D6: answering 403 would reveal that the id exists.
    assert response.status_code == 404
    assert response.json() == missing.json() == {"detail": "Analysis not found"}


def test_report_of_another_user_looks_like_a_missing_one(client, as_user, make_dataset):
    _, _, analysis = make_dataset(USER_A)
    # The owner gets past the ownership check: the pending analysis has no report yet.
    owner = client.get(f"/api/analyses/{analysis.id}/report.pdf")
    assert owner.status_code == 409
    assert owner.json() == {"detail": "Analysis not completed yet"}

    as_user(USER_B)
    response = client.get(f"/api/analyses/{analysis.id}/report.pdf")
    missing = client.get(f"/api/analyses/{uuid.uuid4()}/report.pdf")

    assert response.status_code == 404
    assert response.json() == missing.json() == {"detail": "Analysis not found"}


def test_report_of_a_dataset_whose_name_contains_markup_is_generated(
    client, as_user, db_session, make_dataset
):
    _, dataset, analysis = make_dataset(USER_A, status="completed")
    dataset.filename = "<b>ventas.csv"
    analysis.profile_json = {"row_count": 2, "column_count": 1, "columns": []}
    db_session.flush()

    response = client.get(f"/api/analyses/{analysis.id}/report.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def _report_headers(client, db_session, make_dataset, filename: str):
    _, dataset, analysis = make_dataset(USER_A, status="completed")
    dataset.filename = filename
    analysis.profile_json = {"row_count": 2, "column_count": 1, "columns": []}
    db_session.flush()
    response = client.get(f"/api/analyses/{analysis.id}/report.pdf")
    assert response.status_code == 200
    return response.headers


def test_report_download_name_keeps_the_previous_rule_for_plain_names(
    client, as_user, db_session, make_dataset
):
    headers = _report_headers(client, db_session, make_dataset, "ventas enero.csv")

    assert headers["content-disposition"] == (
        "attachment; filename=\"informe_ventas_enero.pdf\"; "
        "filename*=UTF-8''informe_ventas_enero.pdf"
    )


def test_report_download_name_with_non_latin1_characters_is_encoded(
    client, as_user, db_session, make_dataset
):
    # Headers travel as latin-1: a raw "€" used to make the download fail with a 500.
    headers = _report_headers(client, db_session, make_dataset, "informe €.csv")

    assert headers["content-disposition"] == (
        "attachment; filename=\"informe_informe__.pdf\"; "
        "filename*=UTF-8''informe_informe_%E2%82%AC.pdf"
    )


def test_report_download_name_cannot_inject_header_parameters(
    client, as_user, db_session, make_dataset
):
    hostile = "a\";filename*=UTF-8''evil.exe;x=\".csv"

    headers = _report_headers(client, db_session, make_dataset, hostile)

    assert headers["content-disposition"] == (
        "attachment; filename=\"informe_a__filename__UTF-8__evil.exe_x__.pdf\"; "
        "filename*=UTF-8''informe_a%22%3Bfilename%2A%3DUTF-8%27%27evil.exe%3Bx%3D%22.pdf"
    )


@pytest.mark.parametrize(
    "filename, expected",
    [
        # Only the final extension goes, whatever its case (S7).
        ("VENTAS.CSV", "attachment; filename=\"informe_VENTAS.pdf\"; "
                       "filename*=UTF-8''informe_VENTAS.pdf"),
        ("a.csv.csv", "attachment; filename=\"informe_a.csv.pdf\"; "
                      "filename*=UTF-8''informe_a.csv.pdf"),
        # A CR/LF can never split the header.
        ("a\r\nSet-Cookie: x=1.csv", "attachment; filename=\"informe_a__Set-Cookie__x_1.pdf\"; "
                                    "filename*=UTF-8''informe_a%0D%0ASet-Cookie%3A_x%3D1.pdf"),
        # RFC 5987 does not allow a raw "/" in filename*.
        ("../../otro/ventas.csv", "attachment; filename=\"informe_.._.._otro_ventas.pdf\"; "
                                  "filename*=UTF-8''informe_..%2F..%2Fotro%2Fventas.pdf"),
    ],
    ids=["uppercase-extension", "csv-inside-the-name", "crlf", "slashes"],
)
def test_report_download_name_edge_cases(
    client, as_user, db_session, make_dataset, filename, expected
):
    headers = _report_headers(client, db_session, make_dataset, filename)

    assert headers["content-disposition"] == expected


NEW_FORECAST = {
    "target_column": "ventas",
    "date_column": "fecha",
    "aggregation": "sum",
    "frequency": "M",
    "horizon": 12,
    "wape": 9.67,
    "mae": 268.46,
    "points": [{"ds": "2025-01-01", "yhat": 160.0, "yhat_lower": 140.0, "yhat_upper": 180.0}],
}
# Analyses stored before the forecast quality PR.
OLD_FORECAST = {
    "target_column": "ventas",
    "date_column": "fecha",
    "mape": 8.96,
    "horizon_days": 30,
    "points": [{"ds": "2024-02-01", "yhat": 160.0, "yhat_lower": 140.0, "yhat_upper": 180.0}],
}


@pytest.mark.parametrize(
    ("stored", "expected_extra"),
    [
        (NEW_FORECAST, {"mape": None, "horizon_days": None}),
        (
            OLD_FORECAST,
            {"aggregation": None, "frequency": None, "horizon": None, "wape": None, "mae": None},
        ),
    ],
    ids=["new", "old"],
)
def test_analysis_returns_the_stored_forecast_fields(
    client, as_user, db_session, make_dataset, stored, expected_extra
):
    _, _, analysis = make_dataset(USER_A, status="completed")
    analysis.predictions_json = {"forecast": stored, "regression": None}
    db_session.flush()

    response = client.get(f"/api/analyses/{analysis.id}")

    assert response.status_code == 200
    assert response.json()["predictions"]["forecast"] == {**stored, **expected_extra}
