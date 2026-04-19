from pydantic import BaseModel


class InsightItem(BaseModel):
    title: str
    description: str
    columns: list[str] = []


class InsightsOut(BaseModel):
    trends: list[InsightItem] = []
    anomalies: list[InsightItem] = []
    correlations: list[InsightItem] = []
    recommendations: list[InsightItem] = []
