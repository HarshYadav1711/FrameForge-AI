import logging

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import get_job_store, get_orchestrator
from app.config import get_settings
from app.core.exceptions import JobNotFoundError, JobNotReadyError
from app.models.schemas import (
    CreateJobResponse,
    JobStatus,
    JobStatusResponse,
)
from app.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])

ALLOWED_AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
MAX_AUDIO_BYTES = 50 * 1024 * 1024  # 50 MB


def _to_status_response(job_id: str) -> JobStatusResponse:
    store = get_job_store()
    record = store.get(job_id)
    settings = get_settings()
    video_url = None
    if record.status == JobStatus.COMPLETED:
        video_url = f"/api/v1/jobs/{job_id}/video"

    return JobStatusResponse(
        id=record.id,
        status=record.status,
        progress=record.progress,
        created_at=record.created_at,
        updated_at=record.updated_at,
        error=record.error,
        scenes_count=len(record.scenes) if record.scenes else None,
        video_url=video_url,
        duration_seconds=record.duration_seconds,
    )


async def _run_pipeline(job_id: str) -> None:
    orchestrator = get_orchestrator()
    try:
        await orchestrator.run(job_id)
    except Exception:
        logger.exception("Background pipeline error for %s", job_id)


@router.post("", response_model=CreateJobResponse, status_code=202)
async def create_job(
    background_tasks: BackgroundTasks,
    script: str = Form(..., min_length=10, max_length=50_000),
    audio: UploadFile = File(...),
) -> CreateJobResponse:
    filename = audio.filename or "audio.wav"
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ".wav"
    if suffix not in ALLOWED_AUDIO:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Allowed: {', '.join(sorted(ALLOWED_AUDIO))}",
        )

    content = await audio.read()
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=400, detail="Audio file exceeds 50 MB limit")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    store = get_job_store()
    record = store.create(script=script.strip(), audio_filename=filename)
    paths = store.job_paths(record.id)

    PipelineOrchestrator.save_upload(content, paths["audio"], filename)

    background_tasks.add_task(_run_pipeline, record.id)

    return CreateJobResponse(
        id=record.id,
        status=JobStatus.PENDING,
        message="Processing started",
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str) -> JobStatusResponse:
    try:
        return _to_status_response(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.get("/{job_id}/video")
async def download_video(job_id: str) -> FileResponse:
    store = get_job_store()
    try:
        record = store.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    if record.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail="Video is not ready yet",
        )

    output = store.job_paths(job_id)["output"]
    if not output.exists():
        raise HTTPException(status_code=404, detail="Output file missing")

    return FileResponse(
        path=output,
        media_type="video/mp4",
        filename=f"frameforge-{job_id[:8]}.mp4",
    )
