import uuid

from app.db.models import Project
from tests.conftest import USER_A, USER_B


def _snapshot(db_session, project: Project) -> tuple[str, str | None]:
    db_session.expire_all()
    stored = db_session.get(Project, project.id)
    assert stored is not None
    return stored.name, stored.description


def test_request_without_a_bearer_token_is_unauthorized(client):
    response = client.get("/api/projects")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_project_of_another_user_looks_like_a_missing_one(client, as_user, make_project):
    project = make_project(USER_A)
    assert client.get(f"/api/projects/{project.id}").status_code == 200

    as_user(USER_B)
    response = client.get(f"/api/projects/{project.id}")
    missing = client.get(f"/api/projects/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == missing.json() == {"detail": "Project not found"}
    assert client.get("/api/projects").json() == []


def test_user_cannot_edit_a_project_of_another_user(
    client, as_user, db_session, make_project
):
    project = make_project(USER_A)
    before = _snapshot(db_session, project)
    as_user(USER_B)

    response = client.patch(
        f"/api/projects/{project.id}", json={"name": "Hacked", "description": "Hacked"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    assert _snapshot(db_session, project) == before


def test_user_cannot_delete_a_project_of_another_user(
    client, as_user, db_session, make_project
):
    project = make_project(USER_A)
    before = _snapshot(db_session, project)
    as_user(USER_B)

    response = client.delete(f"/api/projects/{project.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    assert _snapshot(db_session, project) == before
