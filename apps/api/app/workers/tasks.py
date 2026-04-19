import uuid
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import Analysis, Dataset
from app.services.profiling import profile_csv
from app.storage.supabase_client import download_file


def _run_predictions(content: bytes, profile: dict) -> dict | None:
    date_col: str | None = profile.get("date_column_candidate")
    columns: list[dict] = profile.get("columns", [])
    numeric_cols = [c["name"] for c in columns if c["type"] == "numeric"]

    if not numeric_cols:
        return None

    if date_col and len(numeric_cols) >= 1:
        from app.services.forecasting import run_forecast
        target = numeric_cols[0]
        try:
            forecast = run_forecast(content, date_col, target, horizon_days=30)
            return {"forecast": forecast, "regression": None}
        except Exception as exc:
            print(f"[tasks] forecast failed (non-fatal): {exc}", flush=True)

    if len(numeric_cols) >= 2:
        from app.services.ml_baseline import run_regression
        target = numeric_cols[-1]
        features = [c for c in numeric_cols if c != target]
        cat_cols = [c["name"] for c in columns if c["type"] in ("categorical", "boolean")]
        all_features = features + cat_cols
        try:
            regression = run_regression(content, target, all_features)
            return {"forecast": None, "regression": regression}
        except Exception as exc:
            print(f"[tasks] regression failed (non-fatal): {exc}", flush=True)

    return None


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def run_analysis(self, analysis_id: str) -> None:
    db = SessionLocal()
    analysis = None
    try:
        analysis = db.query(Analysis).filter(Analysis.id == uuid.UUID(analysis_id)).first()
        if not analysis:
            return

        analysis.status = "running"
        analysis.started_at = datetime.now(timezone.utc)
        db.commit()

        dataset = db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {analysis.dataset_id} not found")

        content = download_file(dataset.storage_path)
        profile = profile_csv(content)

        dataset.row_count = profile["row_count"]
        dataset.column_count = profile["column_count"]

        # LLM insights — failure is non-fatal
        try:
            from app.services.insights_llm import generate_insights
            insights = generate_insights(profile)
        except Exception as llm_exc:
            print(f"[tasks] LLM insights failed (non-fatal): {llm_exc}", flush=True)
            from app.schemas.insights import InsightsOut
            insights = InsightsOut().model_dump()

        # Predictions — failure is non-fatal
        predictions = None
        try:
            predictions = _run_predictions(content, profile)
        except Exception as pred_exc:
            print(f"[tasks] predictions failed (non-fatal): {pred_exc}", flush=True)

        analysis.status = "completed"
        analysis.profile_json = profile
        analysis.insights_json = insights
        analysis.predictions_json = predictions
        analysis.finished_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        db.rollback()
        if analysis is not None:
            try:
                analysis.status = "failed"
                analysis.error_message = str(exc)
                analysis.finished_at = datetime.now(timezone.utc)
                db.commit()
            except Exception:
                db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()
