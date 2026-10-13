import logging
import uuid
from unittest.mock import MagicMock

from app.db.models import Analysis, Dataset, Project
from app.routers import datasets
from app.workers import tasks
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


def test_storage_failure_hides_its_details_and_persists_nothing(
    client, as_user, db_session, monkeypatch, caplog
):
    project = Project(user_id=USER_A, name="Ventas")
    db_session.add(project)
    db_session.flush()

    def failing_upload(storage_path: str, content: bytes) -> None:
        raise RuntimeError("bucket datainsight unreachable at https://example.supabase.co")

    monkeypatch.setattr(datasets, "upload_file", failing_upload)
    enqueued = MagicMock()
    monkeypatch.setattr(tasks.run_analysis, "delay", enqueued)

    with caplog.at_level(logging.ERROR, logger="app.routers.datasets"):
        response = client.post(
            f"/api/projects/{project.id}/datasets",
            files={"file": ("ventas.csv", b"fecha,ventas\n2024-01-01,100\n", "text/csv")},
        )

    # P4: the client gets a generic message; the detail goes to the log only.
    assert response.status_code == 500
    assert response.json() == {"detail": "Storage upload failed"}
    assert [(r.levelno, r.getMessage(), r.exc_info) for r in caplog.records] == [
        (
            logging.ERROR,
            "Storage upload failed: RuntimeError: "
            "bucket datainsight unreachable at https://example.supabase.co",
            None,
        )
    ]
    assert db_session.query(Dataset).count() == 0
    assert db_session.query(Analysis).count() == 0
    enqueued.assert_not_called()
