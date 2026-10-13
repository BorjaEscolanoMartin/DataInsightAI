import logging
import uuid
from unittest.mock import MagicMock

import pytest

from app.db.models import Analysis, Dataset, Project
from app.routers import datasets
from app.workers import tasks
from tests.conftest import USER_A, USER_B

CSV = b"fecha,ventas\n2024-01-01,100\n2024-01-02,120\n"


@pytest.fixture
def storage(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    upload = MagicMock()
    monkeypatch.setattr(datasets, "upload_file", upload)
    return upload


@pytest.fixture
def enqueued(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    delay = MagicMock()
    monkeypatch.setattr(tasks.run_analysis, "delay", delay)
    return delay


def _stored(db_session, project: Project) -> tuple[int, int]:
    """Datasets and analyses stored for this project only."""
    dataset_count = db_session.query(Dataset).filter(Dataset.project_id == project.id).count()
    analysis_count = (
        db_session.query(Analysis)
        .join(Dataset, Analysis.dataset_id == Dataset.id)
        .filter(Dataset.project_id == project.id)
        .count()
    )
    return dataset_count, analysis_count


def _upload(client, project_id: uuid.UUID, filename: str = "ventas.csv", content: bytes = CSV):
    return client.post(
        f"/api/projects/{project_id}/datasets",
        files={"file": (filename, content, "text/csv")},
    )


def test_dataset_of_another_user_looks_like_a_missing_one(client, as_user, make_dataset):
    _, dataset, analysis = make_dataset(USER_A)
    owner = client.get(f"/api/datasets/{dataset.id}")
    assert owner.status_code == 200
    assert owner.json()["dataset"]["id"] == str(dataset.id)
    assert owner.json()["analysis"]["id"] == str(analysis.id)

    as_user(USER_B)
    response = client.get(f"/api/datasets/{dataset.id}")
    missing = client.get(f"/api/datasets/{uuid.uuid4()}")

    # D6: answering 403 would reveal that the id exists.
    assert response.status_code == 404
    assert response.json() == missing.json() == {"detail": "Dataset not found"}


def test_storage_failure_hides_its_details_and_persists_nothing(
    client, as_user, db_session, make_project, enqueued, monkeypatch, caplog
):
    project = make_project(USER_A)

    def failing_upload(storage_path: str, content: bytes) -> None:
        raise RuntimeError("bucket datainsight unreachable at https://example.supabase.co")

    monkeypatch.setattr(datasets, "upload_file", failing_upload)

    with caplog.at_level(logging.ERROR, logger="app.routers.datasets"):
        response = _upload(client, project.id)

    # P4: the client gets a generic message; the detail goes to the log only.
    assert response.status_code == 500
    assert response.json() == {"detail": "Storage upload failed"}
    records = [r for r in caplog.records if r.name == "app.routers.datasets"]
    assert [(r.levelno, r.getMessage(), r.exc_info) for r in records] == [
        (
            logging.ERROR,
            "Storage upload failed: RuntimeError: "
            "bucket datainsight unreachable at https://example.supabase.co",
            None,
        )
    ]
    assert _stored(db_session, project) == (0, 0)
    enqueued.assert_not_called()


def test_upload_stores_the_dataset_and_queues_its_analysis(
    client, as_user, db_session, make_project, storage, enqueued
):
    project = make_project(USER_A)

    response = _upload(client, project.id)

    assert response.status_code == 201
    body = response.json()
    dataset_id = body["dataset"]["id"]
    analysis_id = body["analysis"]["id"]
    assert body["dataset"]["project_id"] == str(project.id)
    assert body["dataset"]["filename"] == "ventas.csv"
    assert body["dataset"]["size_bytes"] == len(CSV)
    assert body["analysis"]["dataset_id"] == dataset_id
    assert body["analysis"]["status"] == "pending"
    storage.assert_called_once_with(f"{USER_A}/{project.id}/{dataset_id}.csv", CSV)
    enqueued.assert_called_once_with(analysis_id)
    assert _stored(db_session, project) == (1, 1)
    dataset = db_session.get(Dataset, uuid.UUID(dataset_id))
    assert dataset is not None
    assert dataset.storage_path == f"{USER_A}/{project.id}/{dataset_id}.csv"
    analysis = db_session.get(Analysis, uuid.UUID(analysis_id))
    assert analysis is not None and analysis.status == "pending"


def test_upload_rejects_a_file_that_is_not_csv(
    client, as_user, db_session, make_project, storage, enqueued
):
    project = make_project(USER_A)

    response = _upload(client, project.id, filename="ventas.xlsx")

    assert response.status_code == 422
    assert response.json() == {"detail": "Only .csv files are accepted"}
    assert _stored(db_session, project) == (0, 0)
    storage.assert_not_called()
    enqueued.assert_not_called()


def test_upload_accepts_a_file_of_exactly_the_size_limit(
    client, as_user, db_session, make_project, storage, enqueued, monkeypatch
):
    project = make_project(USER_A)
    monkeypatch.setattr(datasets, "MAX_FILE_SIZE", len(CSV))

    assert _upload(client, project.id).status_code == 201
    assert _stored(db_session, project) == (1, 1)


def test_upload_rejects_a_file_over_the_size_limit(
    client, as_user, db_session, make_project, storage, enqueued, monkeypatch
):
    project = make_project(USER_A)
    # Shrinks the 50 MB limit instead of sending 50 MB.
    monkeypatch.setattr(datasets, "MAX_FILE_SIZE", len(CSV) - 1)

    response = _upload(client, project.id)

    assert response.status_code == 422
    assert response.json() == {"detail": "File exceeds 50 MB limit"}
    assert _stored(db_session, project) == (0, 0)
    storage.assert_not_called()
    enqueued.assert_not_called()


def test_upload_to_a_project_of_another_user_looks_like_a_missing_one(
    client, as_user, db_session, make_project, storage, enqueued
):
    project = make_project(USER_A)
    as_user(USER_B)

    response = _upload(client, project.id)
    missing = _upload(client, uuid.uuid4())

    assert response.status_code == 404
    assert response.json() == missing.json() == {"detail": "Project not found"}
    assert _stored(db_session, project) == (0, 0)
    storage.assert_not_called()
    enqueued.assert_not_called()


def test_storage_path_never_contains_the_uploaded_filename(
    client, as_user, db_session, make_project, storage, enqueued
):
    project = make_project(USER_A)
    hostile = "../../otro/ventas.csv"

    response = _upload(client, project.id, filename=hostile)

    assert response.status_code == 201
    dataset_id = response.json()["dataset"]["id"]
    expected_path = f"{USER_A}/{project.id}/{dataset_id}.csv"
    storage.assert_called_once_with(expected_path, CSV)
    dataset = db_session.get(Dataset, uuid.UUID(dataset_id))
    assert dataset is not None
    assert (dataset.storage_path, dataset.filename) == (expected_path, hostile)
    assert response.json()["dataset"]["filename"] == hostile


def test_upload_rejects_a_filename_longer_than_255_characters(
    client, as_user, db_session, make_project, storage, enqueued
):
    project = make_project(USER_A)
    filename = "v" * 252 + ".csv"  # 256 characters

    response = _upload(client, project.id, filename=filename)

    assert response.status_code == 422
    assert response.json() == {"detail": "Filename exceeds 255 characters"}
    assert _stored(db_session, project) == (0, 0)
    storage.assert_not_called()
    enqueued.assert_not_called()


def test_upload_accepts_a_filename_of_exactly_255_characters(
    client, as_user, db_session, make_project, storage, enqueued
):
    project = make_project(USER_A)
    filename = "v" * 251 + ".csv"  # 255 characters

    response = _upload(client, project.id, filename=filename)

    assert response.status_code == 201
    assert response.json()["dataset"]["filename"] == filename
    assert _stored(db_session, project) == (1, 1)


def test_filename_limit_counts_characters_not_bytes(
    client, as_user, db_session, make_project, storage, enqueued
):
    project = make_project(USER_A)
    filename = "é" * 251 + ".csv"  # 255 characters, 506 bytes in UTF-8

    response = _upload(client, project.id, filename=filename)

    assert response.status_code == 201
    assert response.json()["dataset"]["filename"] == filename
