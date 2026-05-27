import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.core.exceptions import JobNotFoundError
from app.models.schemas import JobProgress, JobRecord, JobStatus, PipelineStep

logger = logging.getLogger(__name__)


class JobStore:
    """File-backed job persistence — no database required."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._jobs_root = settings.jobs_path
        self._jobs_root.mkdir(parents=True, exist_ok=True)

    def _job_dir(self, job_id: str) -> Path:
        return self._jobs_root / job_id

    def _meta_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"

    def create(
        self,
        script: str,
        audio_filename: str,
        *,
        upload_id: str | None = None,
    ) -> JobRecord:
        job_id = str(uuid4())
        job_dir = self._job_dir(job_id)
        job_dir.mkdir(parents=True)
        (job_dir / "scenes").mkdir(exist_ok=True)
        (job_dir / "visuals").mkdir(exist_ok=True)

        now = datetime.now(timezone.utc)
        record = JobRecord(
            id=job_id,
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
            script=script,
            audio_filename=audio_filename,
            metadata={"upload_id": upload_id} if upload_id else {},
        )
        self.save(record)
        logger.info("Created job %s", job_id)
        return record

    def get(self, job_id: str) -> JobRecord:
        path = self._meta_path(job_id)
        if not path.exists():
            raise JobNotFoundError(job_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return JobRecord.model_validate(data)

    def save(self, record: JobRecord) -> None:
        record.updated_at = datetime.now(timezone.utc)
        path = self._meta_path(record.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            record.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        *,
        progress: JobProgress | None = None,
        error: str | None = None,
    ) -> JobRecord:
        record = self.get(job_id)
        record.status = status
        if progress is not None:
            record.progress = progress
        if error is not None:
            record.error = error
        self.save(record)
        return record

    def set_step(
        self,
        job_id: str,
        step: PipelineStep,
        percent: int,
        message: str,
    ) -> JobRecord:
        status_map = {
            PipelineStep.TRANSCRIBE: JobStatus.TRANSCRIBING,
            PipelineStep.SEGMENT: JobStatus.SEGMENTING,
            PipelineStep.VISUALS: JobStatus.ATTACHING_VISUALS,
            PipelineStep.SUBTITLES: JobStatus.GENERATING_SUBTITLES,
            PipelineStep.RENDER: JobStatus.RENDERING,
        }
        return self.update_status(
            job_id,
            status_map[step],
            progress=JobProgress(step=step, percent=percent, message=message),
        )

    def set_transcription_progress(
        self,
        job_id: str,
        *,
        percent: int,
        message: str,
        segments_completed: int = 0,
        phase: str = "transcribing",
    ) -> JobRecord:
        """Update job progress during the transcription step."""
        record = self.get(job_id)
        pipeline_percent = 10 + int(percent * 0.2)
        record.progress = JobProgress(
            step=PipelineStep.TRANSCRIBE,
            percent=min(30, pipeline_percent),
            message=message,
        )
        record.status = JobStatus.TRANSCRIBING
        record.metadata["transcription_progress"] = {
            "phase": phase,
            "percent": percent,
            "segments_completed": segments_completed,
        }
        self.save(record)
        return record

    def job_paths(self, job_id: str) -> dict[str, Path]:
        base = self._job_dir(job_id)
        return {
            "root": base,
            "audio": base / "audio",
            "scenes": base / "scenes",
            "visuals": base / "visuals",
            "subtitles": base / "subtitles.srt",
            "output": base / "output.mp4",
            "transcript": base / "transcript.json",
        }
