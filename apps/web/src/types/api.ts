export interface Project {
  id: string
  user_id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
}

export interface ColumnProfile {
  name: string
  type: "numeric" | "categorical" | "date" | "text" | "boolean"
  null_count: number
  null_pct: number
  unique_count: number
  mean?: number
  std?: number
  min_val?: number
  max_val?: number
  p25?: number
  p50?: number
  p75?: number
  outlier_count?: number
  top_categories?: { value: string; count: number }[]
}

export interface ChartSpec {
  id: string
  type: "histogram" | "bar" | "line" | "heatmap" | "scatter"
  title: string
  column?: string
  x_column?: string
  y_column?: string
  columns?: string[]
  data: Record<string, unknown>[]
}

export interface DatasetProfile {
  row_count: number
  column_count: number
  columns: ColumnProfile[]
  date_column_candidate: string | null
  charts: ChartSpec[]
}

export interface Dataset {
  id: string
  project_id: string
  filename: string
  size_bytes: number
  row_count: number | null
  column_count: number | null
  uploaded_at: string
}

export interface InsightItem {
  title: string
  description: string
  columns: string[]
}

export interface Insights {
  trends: InsightItem[]
  anomalies: InsightItem[]
  correlations: InsightItem[]
  recommendations: InsightItem[]
}

export interface Analysis {
  id: string
  dataset_id: string
  status: string
  profile: DatasetProfile | null
  insights: Insights | null
  predictions: PredictionsOut | null
  started_at: string | null
  finished_at: string | null
}

export interface DatasetWithAnalysis {
  dataset: Dataset
  analysis: Analysis
}

export interface ForecastPoint {
  ds: string
  yhat: number
  yhat_lower: number
  yhat_upper: number
}

export interface ForecastOut {
  target_column: string
  date_column: string
  mape: number | null
  horizon_days: number
  points: ForecastPoint[]
}

export interface FeatureImportanceItem {
  feature: string
  importance: number
}

export interface RegressionOut {
  target_column: string
  r2: number
  rmse: number
  feature_importance: FeatureImportanceItem[]
}

export interface PredictionsOut {
  forecast: ForecastOut | null
  regression: RegressionOut | null
}

export interface ApiError {
  detail: string
  code?: string
}
