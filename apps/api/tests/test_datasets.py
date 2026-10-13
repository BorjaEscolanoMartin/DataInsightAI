import uuid

from tests.conftest import USER_A, USER_B


def test_dataset_of_another_user_looks_like_a_missing_one(client, as_user, make_dataset):
    _, dataset, _ = make_dataset(USER_A)
    assert client.get(f"/api/datasets/{dataset.id}").status_code == 200

    as_user(USER_B)
    response = client.get(f"/api/datasets/{dataset.id}")
    missing = client.get(f"/api/datasets/{uuid.uuid4()}")

    # D6: answering 403 would reveal that the id exists.
    assert response.status_code == 404
    assert response.json() == missing.json() == {"detail": "Dataset not found"}
