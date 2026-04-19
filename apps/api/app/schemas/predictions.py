from pydantic import BaseModel


class ForecastPoint(BaseModel):
    ds: str
    yhat: float
    yhat_lower: float
    yhat_upper: float


class ForecastOut(BaseModel):
    target_column: str
    date_column: str
    mape: float | None = None
    horizon_days: int = 30
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
