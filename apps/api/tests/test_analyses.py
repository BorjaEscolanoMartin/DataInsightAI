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
