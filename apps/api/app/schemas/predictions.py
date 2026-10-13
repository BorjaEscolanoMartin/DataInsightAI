from typing import Literal

from pydantic import BaseModel


class ForecastPoint(BaseModel):
    ds: str
    yhat: float
    yhat_lower: float
    yhat_upper: float


class ForecastOut(BaseModel):
    target_column: str
    date_column: str
    aggregation: Literal["none", "sum"] | None = None
    frequency: Literal["D", "W", "M", "Q", "Y"] | None = None
    horizon: int | None = None
    wape: float | None = None
    mae: float | None = None
    # Only in analyses stored before the forecast measured WAPE and MAE per frequency.
    mape: float | None = None
    horizon_days: int | None = None
    points: list[ForecastPoint] = []


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float


class RegressionOut(BaseModel):
    target_column: str
    r2: float
    rmse: float
    feature_importance: list[FeatureImportanceItem] = []


class PredictionsOut(BaseModel):
    forecast: ForecastOut | None = None
    regression: RegressionOut | None = None
