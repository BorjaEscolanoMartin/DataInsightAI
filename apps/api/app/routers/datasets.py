import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Project, Dataset, Analysis
from app.auth import get_current_user
from app.schemas.datasets import DatasetOut, AnalysisOut, DatasetWithAnalysisOut, DatasetProfileOut
from app.storage.supabase_client import upload_file

router = APIRouter(tags=["datasets"])

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

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=422, detail="File exceeds 50 MB limit")

    dataset_id = uuid.uuid4()
    storage_path = f"{user_id}/{project_id}/{dataset_id}/{file.filename}"

    try:
        upload_file(storage_path, content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {e}")

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
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    project = db.query(Project).filter(Project.id == dataset.project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=403, detail="Forbidden")

    analysis = (
        db.query(Analysis)
        .filter(Analysis.dataset_id == dataset_id)
        .order_by(Analysis.started_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return _build_response(dataset, analysis)
