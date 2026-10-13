import uuid

from tests.conftest import USER_A, USER_B


def test_analysis_of_another_user_looks_like_a_missing_one(client, as_user, make_dataset):
    _, _, analysis = make_dataset(USER_A)
    assert client.get(f"/api/analyses/{analysis.id}").status_code == 200

    as_user(USER_B)
    response = client.get(f"/api/analyses/{analysis.id}")
    missing = client.get(f"/api/analyses/{uuid.uuid4()}")

    # D6: answering 403 would reveal that the id exists.
    assert response.status_code == 404
    assert response.json() == missing.json() == {"detail": "Analysis not found"}


def test_report_of_another_user_looks_like_a_missing_one(client, as_user, make_dataset):
    _, _, analysis = make_dataset(USER_A)
    # The owner gets past the ownership check: the pending analysis has no report yet.
    assert client.get(f"/api/analyses/{analysis.id}/report.pdf").status_code == 409

    as_user(USER_B)
    response = client.get(f"/api/analyses/{analysis.id}/report.pdf")
    missing = client.get(f"/api/analyses/{uuid.uuid4()}/report.pdf")

    assert response.status_code == 404
    assert response.json() == missing.json() == {"detail": "Analysis not found"}
