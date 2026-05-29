import logging

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import get_job_store, get_orchestrator, get_upload_service
from app.core.exceptions import InvalidAudioError, JobNotFoundError, UploadNotFoundError
from app.models.schemas import (
    CreateJobResponse,
    JobRecord,
    JobStatus,
    JobStatusResponse,
    ScenesResponse,
    SegmentationStatusSummary,
    TranscriptionMetadata,
    TranscriptionStatusSummary,
    TranscriptResponse,
)
from app.services.segmentation.base import build_segmentation_result
from app.services.segmentation.formats import read_scenes_artifact
from app.services.transcription.base import build_transcript_result
from app.services.transcription.formats import read_transcript_artifact

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


def _transcription_summary(
    job_id: str,
    record: JobRecord,
) -> TranscriptionStatusSummary | None:
    store = get_job_store()
    paths = store.job_paths(job_id)
    meta = record.metadata.get("transcription")

    if meta:
        return TranscriptionStatusSummary(
            available=True,
            segment_count=meta.get("segment_count"),
            duration_seconds=meta.get("duration_seconds"),
            language=meta.get("language"),
            language_probability=meta.get("language_probability"),
            model=meta.get("model"),
            backend=meta.get("backend"),
        )

    if record.transcript:
        return TranscriptionStatusSummary(
            available=True,
            segment_count=len(record.transcript),
            duration_seconds=record.duration_seconds,
        )

    if paths["transcript"].exists():
        try:
            artifact = read_transcript_artifact(paths["transcript"])
            m = artifact.metadata
            return TranscriptionStatusSummary(
                available=True,
                segment_count=m.segment_count,
                duration_seconds=m.duration_seconds,
                language=m.language,
                language_probability=m.language_probability,
                model=m.model,
                backend=m.backend,
            )
        except Exception:
            logger.warning("Could not read transcript artifact for %s", job_id)

    return None


def _segmentation_summary(
    job_id: str,
    record: JobRecord,
) -> SegmentationStatusSummary | None:
    store = get_job_store()
    paths = store.job_paths(job_id)
    meta = record.metadata.get("segmentation")

    if meta:
        return SegmentationStatusSummary(
            available=True,
            scene_count=meta.get("scene_count"),
            source=meta.get("source"),
            timeline_aligned=meta.get("timeline_aligned"),
            total_duration_seconds=meta.get("total_duration_seconds"),
        )

    if record.scenes:
        return SegmentationStatusSummary(
            available=True,
            scene_count=len(record.scenes),
            timeline_aligned=any(
                s.start_time is not None for s in record.scenes
            ),
            total_duration_seconds=record.duration_seconds,
        )

    if paths["scenes_artifact"].exists():
        try:
            artifact = read_scenes_artifact(paths["scenes_artifact"])
            m = artifact.metadata
            return SegmentationStatusSummary(
                available=True,
                scene_count=m.scene_count,
                source=m.source,
                timeline_aligned=m.timeline_aligned,
                total_duration_seconds=m.total_duration_seconds,
            )
        except Exception:
            logger.warning("Could not read scenes artifact for %s", job_id)

    return None


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
        transcription=_transcription_summary(job_id, record),
        segmentation=_segmentation_summary(job_id, record),
        metadata=record.metadata,
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


@router.get("/{job_id}/transcript", response_model=TranscriptResponse)
async def get_job_transcript(job_id: str) -> TranscriptResponse:
    store = get_job_store()
    try:
        record = store.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    paths = store.job_paths(job_id)
    if paths["transcript"].exists():
        try:
            result = read_transcript_artifact(paths["transcript"])
            return TranscriptResponse(
                job_id=job_id,
                segments=result.segments,
                timeline_blocks=result.timeline_blocks,
                subtitle_cues=result.subtitle_cues,
                metadata=result.metadata,
            )
        except Exception as exc:
            logger.warning("Transcript artifact unreadable for %s: %s", job_id, exc)

    if not record.transcript:
        raise HTTPException(
            status_code=404,
            detail="Transcript not available yet",
        )

    result = build_transcript_result(
        record.transcript,
        TranscriptionMetadata(
            duration_seconds=record.duration_seconds or 0,
            segment_count=len(record.transcript),
        ),
    )
    return TranscriptResponse(
        job_id=job_id,
        segments=result.segments,
        timeline_blocks=result.timeline_blocks,
        subtitle_cues=result.subtitle_cues,
        metadata=result.metadata,
    )


@router.get("/{job_id}/scenes", response_model=ScenesResponse)
async def get_job_scenes(job_id: str) -> ScenesResponse:
    store = get_job_store()
    try:
        record = store.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    paths = store.job_paths(job_id)
    if paths["scenes_artifact"].exists():
        try:
            result = read_scenes_artifact(paths["scenes_artifact"])
            return ScenesResponse(
                job_id=job_id,
                scenes=result.scenes,
                metadata=result.metadata,
            )
        except Exception as exc:
            logger.warning("Scenes artifact unreadable for %s: %s", job_id, exc)

    if not record.scenes:
        raise HTTPException(
            status_code=404,
            detail="Scenes not available yet",
        )

    result = build_segmentation_result(
        record.scenes,
        source="unknown",
        total_duration=record.duration_seconds or 0,
    )
    return ScenesResponse(
        job_id=job_id,
        scenes=result.scenes,
        metadata=result.metadata,
    )


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
