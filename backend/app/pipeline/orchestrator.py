import asyncio
import logging
from pathlib import Path

from app.config import Settings
from app.core.exceptions import (
    PipelineError,
    RenderingError,
    SegmentationError,
    TranscriptionError,
    VisualAssemblyError,
)
from app.models.schemas import JobProgress, JobStatus, PipelineStep, TranscriptionProgress
from app.services.job_store import JobStore
from app.services.rendering import RenderRequest, VideoRenderEngine, get_render_queue
from app.services.segmentation import segment_script
from app.services.subtitles import generate_srt, subtitle_rendering_enabled
from app.services.transcription import transcribe_audio
from app.services.visuals import attach_visuals

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Runs the full video generation pipeline for a single job."""

    def __init__(self, store: JobStore, settings: Settings) -> None:
        self._store = store
        self._settings = settings

    def _transcription_progress_handler(self, job_id: str):
        def on_progress(progress: TranscriptionProgress) -> None:
            self._store.set_transcription_progress(
                job_id,
                percent=progress.percent,
                message=progress.message,
                segments_completed=progress.segments_completed,
                phase=progress.phase,
            )

        return on_progress

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

            try:
                segments, duration = await asyncio.to_thread(
                    transcribe_audio,
                    audio_path,
                    self._settings,
                    transcript_out=paths["transcript"],
                    initial_prompt=record.script[:500] if record.script else None,
                    on_progress=self._transcription_progress_handler(job_id),
                )
            except TranscriptionError as exc:
                logger.error(
                    "Transcription failed for job %s: %s (cause=%s)",
                    job_id,
                    exc.message,
                    exc.cause,
                )
                raise

            record = self._store.get(job_id)
            record.transcript = segments
            record.duration_seconds = duration
            if paths["transcript"].exists():
                from app.services.transcription.formats import read_transcript_artifact

                artifact = read_transcript_artifact(paths["transcript"])
                record.metadata["transcription"] = artifact.metadata.model_dump()
            self._store.save(record)
            self._store.set_step(
                job_id,
                PipelineStep.TRANSCRIBE,
                30,
                f"Transcription complete ({len(segments)} segments)",
            )

            # Step 2: Segment script
            self._store.set_step(
                job_id,
                PipelineStep.SEGMENT,
                30,
                "Segmenting narration into scenes…",
            )
            timeline_blocks = []
            if paths["transcript"].exists():
                from app.services.transcription.formats import read_transcript_artifact

                transcript_artifact = read_transcript_artifact(paths["transcript"])
                timeline_blocks = transcript_artifact.timeline_blocks

            try:
                scenes = await segment_script(
                    record.script,
                    segments,
                    duration,
                    self._settings,
                    timeline_blocks=timeline_blocks,
                    scenes_out=paths["scenes_artifact"],
                )
            except SegmentationError as exc:
                logger.error(
                    "Segmentation failed for job %s: %s (cause=%s)",
                    job_id,
                    exc.message,
                    exc.cause,
                )
                raise

            record = self._store.get(job_id)
            record.scenes = scenes
            if paths["scenes_artifact"].exists():
                from app.services.segmentation.formats import read_scenes_artifact

                seg_artifact = read_scenes_artifact(paths["scenes_artifact"])
                record.metadata["segmentation"] = seg_artifact.metadata.model_dump()
            self._store.save(record)
            self._store.set_step(
                job_id,
                PipelineStep.SEGMENT,
                50,
                f"Segmentation complete ({len(scenes)} scenes)",
            )

            # Step 3: Attach visuals
            self._store.set_step(
                job_id,
                PipelineStep.VISUALS,
                50,
                "Generating scene visuals…",
            )
            try:
                scenes, visual_timeline = await asyncio.to_thread(
                    attach_visuals,
                    scenes,
                    paths["visuals"],
                    self._settings,
                    total_duration=duration,
                )
            except VisualAssemblyError as exc:
                logger.error(
                    "Visual assembly failed for job %s: %s (scene=%s)",
                    job_id,
                    exc.message,
                    exc.scene_index,
                )
                raise

            from app.services.visual_assembly import write_visual_timeline_artifact

            write_visual_timeline_artifact(visual_timeline, paths["visual_timeline"])

            record = self._store.get(job_id)
            record.scenes = scenes
            record.metadata["visual_assembly"] = visual_timeline.metadata.model_dump()
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
            engine = VideoRenderEngine(self._settings)
            render_request = RenderRequest(
                scenes=scenes,
                audio_path=audio_path,
                output_path=paths["output"],
                settings=self._settings,
                srt_path=paths["subtitles"],
                transcript_segments=segments
                if subtitle_rendering_enabled(self._settings)
                else None,
                visual_timeline=visual_timeline,
                job_id=job_id,
                metadata_path=paths["render_output"],
                state_path=paths["render_state"],
                work_dir=paths["render_temp"],
            )

            def on_render_progress(progress):
                self._store.set_rendering_progress(job_id, progress)

            _output_path, render_metadata = await get_render_queue().run(
                lambda: engine.render(
                    render_request, on_progress=on_render_progress
                ),
                job_id=job_id,
            )

            record = self._store.get(job_id)
            record.metadata["render_output"] = render_metadata.model_dump(mode="json")
            self._store.save(record)

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

        except RenderingError as exc:
            logger.exception("Render step failed for job %s", job_id)
            self._store.update_status(
                job_id,
                JobStatus.FAILED,
                error=exc.message,
                progress=JobProgress(
                    step=PipelineStep.RENDER,
                    percent=0,
                    message="Rendering failed",
                ),
            )
            raise PipelineError(exc.message, step="render") from exc

        except VisualAssemblyError as exc:
            logger.exception("Visual assembly step failed for job %s", job_id)
            self._store.update_status(
                job_id,
                JobStatus.FAILED,
                error=exc.message,
                progress=JobProgress(
                    step=PipelineStep.VISUALS,
                    percent=0,
                    message="Visual assembly failed",
                ),
            )
            raise PipelineError(exc.message, step="visuals") from exc

        except SegmentationError as exc:
            logger.exception("Segmentation step failed for job %s", job_id)
            self._store.update_status(
                job_id,
                JobStatus.FAILED,
                error=exc.message,
                progress=JobProgress(
                    step=PipelineStep.SEGMENT,
                    percent=0,
                    message="Segmentation failed",
                ),
            )
            raise PipelineError(exc.message, step="segment") from exc

        except TranscriptionError as exc:
            logger.exception("Transcription step failed for job %s", job_id)
            self._store.update_status(
                job_id,
                JobStatus.FAILED,
                error=exc.message,
                progress=JobProgress(
                    step=PipelineStep.TRANSCRIBE,
                    percent=0,
                    message="Transcription failed",
                ),
            )
            raise PipelineError(exc.message, step="transcribe") from exc

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
