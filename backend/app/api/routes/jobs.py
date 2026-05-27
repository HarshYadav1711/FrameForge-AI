import logging

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import get_job_store, get_orchestrator, get_upload_service
from app.core.exceptions import InvalidAudioError, JobNotFoundError, UploadNotFoundError
from app.models.schemas import CreateJobResponse, JobStatus, JobStatusResponse
from app.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_status_response(job_id: str) -> JobStatusResponse:
    store = get_job_store()
    record = store.get(job_id)
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
    upload_id: str | None = Form(default=None),
    audio: UploadFile | None = File(default=None),
) -> CreateJobResponse:
    if not upload_id and not audio:
        raise HTTPException(
            status_code=400,
            detail="Provide upload_id from /uploads or an audio file",
        )
    if upload_id and audio and audio.filename:
        raise HTTPException(
            status_code=400,
            detail="Provide either upload_id or audio file, not both",
        )

    store = get_job_store()
    upload_service = get_upload_service()
    audio_filename = "audio.wav"

    if upload_id:
        try:
            meta = upload_service.get_meta(upload_id)
        except UploadNotFoundError as exc:
            raise HTTPException(status_code=404, detail=exc.message) from exc
        audio_filename = meta["sanitized_filename"]
        record = store.create(
            script=script.strip(),
            audio_filename=audio_filename,
            upload_id=upload_id,
        )
        paths = store.job_paths(record.id)
        try:
            upload_service.attach_to_job(upload_id, paths["audio"])
        except (UploadNotFoundError, InvalidAudioError) as exc:
            raise HTTPException(status_code=400, detail=exc.message) from exc
    else:
        assert audio is not None
        filename = audio.filename or "audio.wav"
        content = await audio.read()
        try:
            meta = upload_service.save(
                content,
                original_filename=filename,
                content_type=audio.content_type,
            )
        except InvalidAudioError as exc:
            raise HTTPException(status_code=400, detail=exc.message) from exc

        record = store.create(
            script=script.strip(),
            audio_filename=meta["sanitized_filename"],
            upload_id=meta["id"],
        )
        paths = store.job_paths(record.id)
        upload_service.attach_to_job(meta["id"], paths["audio"])

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
        raise HTTPException(status_code=409, detail="Video is not ready yet")

    output = store.job_paths(job_id)["output"]
    if not output.exists():
        raise HTTPException(status_code=404, detail="Output file missing")

    return FileResponse(
        path=output,
        media_type="video/mp4",
        filename=f"frameforge-{job_id[:8]}.mp4",
    )
