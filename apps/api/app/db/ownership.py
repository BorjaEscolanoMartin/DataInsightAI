"""Load a user's datasets and analyses in one query, joined with their project.

A resource that belongs to another user is filtered out by the same query that finds it, so
it follows exactly the same path as a missing one: the API answers 404 for both and never
reveals which ids exist.
"""

import uuid
from typing import Any

from sqlalchemy.orm import Query, Session

from app.db.models import Analysis, Dataset, Project


def _owned_by(query: Query[Any], user_id: uuid.UUID) -> Query[Any]:
    return query.join(Project, Dataset.project_id == Project.id).filter(
        Project.user_id == user_id
    )


def owned_dataset(db: Session, dataset_id: uuid.UUID, user_id: uuid.UUID) -> Dataset | None:
    return _owned_by(db.query(Dataset), user_id).filter(Dataset.id == dataset_id).first()


def owned_analysis(
    db: Session, analysis_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[Analysis, Dataset] | None:
    query = db.query(Analysis, Dataset).join(Dataset, Analysis.dataset_id == Dataset.id)
    row = _owned_by(query, user_id).filter(Analysis.id == analysis_id).first()
    return None if row is None else (row[0], row[1])
