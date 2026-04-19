import uuid
from datetime import datetime
from pydantic import BaseModel
from app.schemas.datasets import DatasetProfileOut
from app.schemas.insights import InsightsOut
from app.schemas.predictions import PredictionsOut


class AnalysisDetailOut(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    status: str
    profile: DatasetProfileOut | None = None
    insights: InsightsOut | None = None
    predictions: PredictionsOut | None = None
    started_at: datetime | None
    finished_at: datetime | None
