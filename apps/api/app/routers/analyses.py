import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db.models import Analysis, Dataset
from app.db.ownership import owned_analysis
from app.db.session import get_db
from app.schemas.analyses import AnalysisDetailOut
from app.schemas.datasets import DatasetProfileOut

router = APIRouter(tags=["analyses"])


@router.get("/api/analyses/{analysis_id}", response_model=AnalysisDetailOut)
def get_analysis(
    analysis_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisDetailOut:
    analysis, _ = _get_analysis_with_auth(analysis_id, user_id, db)

    from app.schemas.insights import InsightsOut
    from app.schemas.predictions import PredictionsOut
    return AnalysisDetailOut(
        id=analysis.id,
        dataset_id=analysis.dataset_id,
        status=analysis.status,
        profile=DatasetProfileOut.model_validate(analysis.profile_json)
        if analysis.profile_json
        else None,
        insights=InsightsOut.model_validate(analysis.insights_json)
        if analysis.insights_json
        else None,
        predictions=PredictionsOut.model_validate(analysis.predictions_json)
        if analysis.predictions_json
        else None,
        started_at=analysis.started_at,
        finished_at=analysis.finished_at,
    )


def _get_analysis_with_auth(
    analysis_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session,
) -> tuple[Analysis, Dataset]:
    owned = owned_analysis(db, analysis_id, user_id)
    if owned is None:
        # Missing and owned by another user look the same (D6).
        raise HTTPException(status_code=404, detail="Analysis not found")
    return owned


@router.get("/api/analyses/{analysis_id}/report.pdf")
def download_report(
    analysis_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    analysis, dataset = _get_analysis_with_auth(analysis_id, user_id, db)

    if analysis.status != "completed":
        raise HTTPException(status_code=409, detail="Analysis not completed yet")
    if not analysis.profile_json:
        raise HTTPException(status_code=409, detail="No profile data available")

    from app.services.report import generate_report
    pdf_bytes = generate_report(
        filename=dataset.filename,
        profile=analysis.profile_json,
        insights=analysis.insights_json,
        predictions=analysis.predictions_json,
    )

    safe_name = dataset.filename.replace(".csv", "").replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="informe_{safe_name}.pdf"'},
    )
