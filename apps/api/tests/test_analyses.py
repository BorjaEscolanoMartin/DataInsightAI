import uuid

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
