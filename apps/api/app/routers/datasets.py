import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db.models import MAX_FILENAME_LENGTH, Analysis, Dataset, Project
from app.db.ownership import owned_dataset
from app.db.session import get_db
from app.schemas.datasets import AnalysisOut, DatasetOut, DatasetProfileOut, DatasetWithAnalysisOut
from app.storage.supabase_client import upload_file

router = APIRouter(tags=["datasets"])
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _build_response(dataset: Dataset, analysis: Analysis) -> DatasetWithAnalysisOut:
    from app.schemas.insights import InsightsOut
    from app.schemas.predictions import PredictionsOut
    return DatasetWithAnalysisOut(
        dataset=DatasetOut.model_validate(dataset),
        analysis=AnalysisOut(
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
        ),
    )


@router.post(
    "/api/projects/{project_id}/datasets",
    response_model=DatasetWithAnalysisOut,
    status_code=201,
)
def upload_dataset(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatasetWithAnalysisOut:
    from app.workers.tasks import run_analysis

    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only .csv files are accepted")
    if len(file.filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(
            status_code=422, detail=f"Filename exceeds {MAX_FILENAME_LENGTH} characters"
        )

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=422, detail="File exceeds 50 MB limit")

    dataset_id = uuid.uuid4()
    # The uploaded filename never reaches Storage: it is only kept in Dataset.filename.
    storage_path = f"{user_id}/{project_id}/{dataset_id}.csv"

    try:
        upload_file(storage_path, content)
    except Exception as e:
        # P4: the client gets a generic message. The log keeps only the exception type and
        # message, never the request or its headers.
        logger.error("Storage upload failed: %s: %s", type(e).__name__, e)
        raise HTTPException(status_code=500, detail="Storage upload failed")

    dataset = Dataset(
        id=dataset_id,
        project_id=project_id,
        filename=file.filename,
        storage_path=storage_path,
        size_bytes=len(content),
    )
    db.add(dataset)
    db.flush()

    analysis = Analysis(
        dataset_id=dataset_id,
        status="pending",
    )
    db.add(analysis)
    db.commit()
    db.refresh(dataset)
    db.refresh(analysis)

    run_analysis.delay(str(analysis.id))

    return _build_response(dataset, analysis)


@router.get("/api/projects/{project_id}/datasets", response_model=list[DatasetWithAnalysisOut])
def list_datasets(
    project_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DatasetWithAnalysisOut]:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    datasets = (
        db.query(Dataset)
        .filter(Dataset.project_id == project_id)
        .order_by(Dataset.uploaded_at.desc())
        .all()
    )

    result = []
    for dataset in datasets:
        analysis = (
            db.query(Analysis)
            .filter(Analysis.dataset_id == dataset.id)
            .order_by(Analysis.started_at.desc())
            .first()
        )
        if analysis:
            result.append(_build_response(dataset, analysis))
    return result


@router.get("/api/datasets/{dataset_id}", response_model=DatasetWithAnalysisOut)
def get_dataset(
    dataset_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatasetWithAnalysisOut:
    dataset = owned_dataset(db, dataset_id, user_id)
    if not dataset:
        # Missing and owned by another user look the same (D6).
        raise HTTPException(status_code=404, detail="Dataset not found")

    analysis = (
        db.query(Analysis)
        .filter(Analysis.dataset_id == dataset_id)
        .order_by(Analysis.started_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return _build_response(dataset, analysis)
