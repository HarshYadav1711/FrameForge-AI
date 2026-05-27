import asyncio
import logging
from pathlib import Path

from app.config import Settings
from app.core.exceptions import PipelineError
from app.models.schemas import JobProgress, JobStatus, PipelineStep
from app.services.job_store import JobStore
from app.services.rendering import render_video
from app.services.segmentation import segment_script
from app.services.subtitles import generate_srt
from app.services.transcription import transcribe_audio
from app.services.visuals import attach_visuals

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Runs the full video generation pipeline for a single job."""

    def __init__(self, store: JobStore, settings: Settings) -> None:
        self._store = store
        self._settings = settings

    async def run(self, job_id: str) -> None:
        paths = self._store.job_paths(job_id)
        record = self._store.get(job_id)

        try:
            # Step 1: Transcribe
            self._store.set_step(
                job_id,
                PipelineStep.TRANSCRIBE,
                10,
                "Transcribing narration audio…",
            )
            audio_candidates = sorted(paths["root"].glob("audio.*"))
            if not audio_candidates:
                raise FileNotFoundError("Uploaded audio file not found")
            audio_path = audio_candidates[0]
            segments, duration = await asyncio.to_thread(
                transcribe_audio,
                audio_path,
                self._settings,
                transcript_out=paths["transcript"],
            )
            record = self._store.get(job_id)
            record.transcript = segments
            record.duration_seconds = duration
            self._store.save(record)

            # Step 2: Segment script
            self._store.set_step(
                job_id,
                PipelineStep.SEGMENT,
                30,
                "Segmenting script into scenes…",
            )
            scenes = await segment_script(
                record.script,
                segments,
                duration,
                self._settings,
            )
            for i, scene in enumerate(scenes):
                scenes[i] = scene.model_copy(update={"index": i})

            record = self._store.get(job_id)
            record.scenes = scenes
            self._store.save(record)

            # Step 3: Attach visuals
            self._store.set_step(
                job_id,
                PipelineStep.VISUALS,
                50,
                "Generating scene visuals…",
            )
            scenes = await asyncio.to_thread(
                attach_visuals,
                scenes,
                paths["visuals"],
                self._settings,
            )
            record = self._store.get(job_id)
            record.scenes = scenes
            self._store.save(record)

            # Step 4: Subtitles
            self._store.set_step(
                job_id,
                PipelineStep.SUBTITLES,
                70,
                "Generating subtitles…",
            )
            await asyncio.to_thread(
                generate_srt,
                segments,
                paths["subtitles"],
            )

            # Step 5: Render
            self._store.set_step(
                job_id,
                PipelineStep.RENDER,
                85,
                "Rendering final video…",
            )
            await asyncio.to_thread(
                render_video,
                scenes,
                audio_path,
                paths["output"],
                self._settings,
                srt_path=paths["subtitles"],
            )

            self._store.update_status(
                job_id,
                JobStatus.COMPLETED,
                progress=JobProgress(
                    step=PipelineStep.RENDER,
                    percent=100,
                    message="Video ready for download",
                ),
            )
            logger.info("Job %s completed", job_id)

        except Exception as exc:
            logger.exception("Pipeline failed for job %s", job_id)
            self._store.update_status(
                job_id,
                JobStatus.FAILED,
                error=str(exc),
                progress=JobProgress(percent=0, message="Pipeline failed"),
            )
            raise PipelineError(str(exc), step="orchestrator") from exc

    @staticmethod
    def save_upload(audio_bytes: bytes, dest: Path, filename: str) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        suffix = Path(filename).suffix or ".wav"
        target = dest.with_suffix(suffix)
        target.write_bytes(audio_bytes)
        return target
