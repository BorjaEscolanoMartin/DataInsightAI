import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.schemas.insights import InsightsOut
from app.schemas.predictions import PredictionsOut


class ColumnProfileOut(BaseModel):
    name: str
    type: str
    null_count: int
    null_pct: float
    unique_count: int
    mean: float | None = None
    std: float | None = None
    min_val: float | None = None
    max_val: float | None = None
    p25: float | None = None
    p50: float | None = None
    p75: float | None = None
    outlier_count: int | None = None
    top_categories: list[dict[str, Any]] | None = None


class ChartSpec(BaseModel):
    id: str
    type: str
    title: str
    column: str | None = None
    x_column: str | None = None
    y_column: str | None = None
    columns: list[str] | None = None
    data: list[dict[str, Any]]


class DatasetProfileOut(BaseModel):
    row_count: int
    column_count: int
    columns: list[ColumnProfileOut]
    date_column_candidate: str | None = None
    charts: list[ChartSpec] = []


class DatasetOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    size_bytes: int
    row_count: int | None
    column_count: int | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    status: str
    profile: DatasetProfileOut | None = None
    insights: InsightsOut | None = None
    predictions: PredictionsOut | None = None
    started_at: datetime | None
    finished_at: datetime | None


class DatasetWithAnalysisOut(BaseModel):
    dataset: DatasetOut
    analysis: AnalysisOut
