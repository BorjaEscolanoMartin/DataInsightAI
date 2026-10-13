import os
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

# Settings require SUPABASE_URL; tests must not depend on a developer's .env.
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
# Environment variables win over apps/api/.env: tests never reach the development database.
# CI sets DATABASE_URL to its Postgres service; locally this needs `docker compose up -d db`
# and a `datainsight_test` database.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/datainsight_test"
)

from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from app.auth import get_current_user  # noqa: E402
from app.config import settings  # noqa: E402
from app.db.models import Analysis, Dataset, Project  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

API_DIR = Path(__file__).resolve().parent.parent

USER_A = uuid.UUID("00000000-0000-4000-8000-00000000000a")
USER_B = uuid.UUID("00000000-0000-4000-8000-00000000000b")


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    """Postgres test database, migrated once per session with the production migrations.

    Without Postgres the tests that need it fail: skipping them would hide it in CI.
    """
    database = make_url(settings.database_url).database or ""
    if not database.endswith("_test"):
        # Every test rolls back, but a wrong URL must never reach a real database.
        pytest.exit(f"Refusing to run against database {database!r}: its name must end in _test")
    engine = create_engine(settings.database_url, connect_args={"connect_timeout": 5})
    # Fail fast, before the migrations, when Postgres is not running.
    engine.connect().close()
    # No alembic.ini: its logging section would disable the loggers other tests capture.
    alembic_config = Config()
    alembic_config.set_main_option("script_location", str(API_DIR / "alembic"))
    command.upgrade(alembic_config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    """A session inside a transaction that is rolled back after the test.

    The routers' commits become savepoints, so nothing a test writes outlives it.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def as_user() -> Iterator[Callable[[uuid.UUID], None]]:
    """Authenticate the next requests as the given user (token checks live in test_auth)."""

    def switch(user_id: uuid.UUID) -> None:
        app.dependency_overrides[get_current_user] = lambda: user_id

    switch(USER_A)
    yield switch
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def make_dataset(
    db_session: Session,
) -> Callable[..., tuple[Project, Dataset, Analysis]]:
    """Store a project with one dataset and its analysis, owned by the given user."""

    def create(user_id: uuid.UUID, status: str = "pending") -> tuple[Project, Dataset, Analysis]:
        project = Project(user_id=user_id, name="Ventas")
        dataset = Dataset(
            project=project,
            filename="ventas.csv",
            storage_path=f"{user_id}/ventas.csv",
            size_bytes=128,
        )
        analysis = Analysis(dataset=dataset, status=status)
        db_session.add_all([project, dataset, analysis])
        db_session.flush()
        return project, dataset, analysis

    return create


@pytest.fixture
def make_project(db_session: Session) -> Callable[[uuid.UUID], Project]:
    """Store an empty project owned by the given user."""

    def create(user_id: uuid.UUID) -> Project:
        project = Project(user_id=user_id, name="Ventas", description="Ventas diarias")
        db_session.add(project)
        db_session.flush()
        return project

    return create
