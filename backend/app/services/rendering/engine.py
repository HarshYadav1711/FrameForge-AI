"""Video render engine — compose, encode, metadata, lifecycle."""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.exceptions import RenderingError
from app.models.schemas import RenderOutputMetadata, RenderPhase, RenderingProgress
from app.services.rendering.cleanup import (
    ClipResourceManager,
    cleanup_render_temp,
    ensure_clean_output_slot,
    promote_partial_output,
    remove_partial_output,
)
from app.services.rendering.composer import compose_video
from app.services.rendering.config import RenderOutputConfig, render_config_from_settings
from app.services.rendering.export import export_video_clip
from app.services.rendering.formats import write_render_output_artifact
from app.services.rendering.lifecycle import RenderLifecycle
from app.services.rendering.metadata import build_output_metadata
from app.services.rendering.progress import ProgressCallback, RenderProgressReporter
from app.services.rendering.recovery import run_with_recovery
from app.services.rendering.request import RenderRequest

logger = logging.getLogger(__name__)


class VideoRenderEngine:
    """Production render pipeline: visuals + subtitles + narration -> MP4."""

    def __init__(self, settings=None) -> None:
        from app.config import Settings

        self._settings = settings or Settings()

    def render(
        self,
        request: RenderRequest,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> tuple[str, RenderOutputMetadata]:
        config = render_config_from_settings(request.settings)
        lifecycle = RenderLifecycle(state_path=request.state_path)

        def _attempt(attempt: int) -> tuple[str, RenderOutputMetadata]:
            return self._render_once(request, config, lifecycle, on_progress, attempt)

        def _on_retry(attempt: int, exc: Exception) -> None:
            lifecycle.mark_attempt(attempt + 1)
            lifecycle.transition(RenderPhase.PREPARING, error=str(exc))
            work_dir = request.resolve_work_dir()
            cleanup_render_temp(work_dir)
            remove_partial_output(request.output_path)

        try:
            return run_with_recovery(_attempt, config, on_retry=_on_retry)
        except RenderingError:
            lifecycle.transition(RenderPhase.FAILED)
            raise

    def _render_once(
        self,
        request: RenderRequest,
        config: RenderOutputConfig,
        lifecycle: RenderLifecycle,
        on_progress: ProgressCallback | None,
        attempt: int,
    ) -> tuple[str, RenderOutputMetadata]:
        work_dir = request.resolve_work_dir()
        reporter = RenderProgressReporter(on_progress, attempt=attempt)
        resources = ClipResourceManager()

        lifecycle.mark_attempt(attempt)
        lifecycle.transition(RenderPhase.PREPARING)
        reporter.report(RenderPhase.PREPARING, 5, "Preparing render…")

        ensure_clean_output_slot(request.output_path)
        cleanup_render_temp(work_dir)

        try:
            lifecycle.transition(RenderPhase.COMPOSING)
            reporter.report(RenderPhase.COMPOSING, 18, "Compositing visuals and subtitles…")

            composed = compose_video(
                request.scenes,
                request.audio_path,
                request.settings,
                config,
                resources,
                srt_path=request.srt_path,
                transcript_segments=request.transcript_segments,
                visual_timeline=request.visual_timeline,
            )

            partial = request.output_path.with_suffix(
                request.output_path.suffix + ".partial"
            )
            lifecycle.set_partial(partial)
            lifecycle.transition(RenderPhase.ENCODING)

            export_video_clip(
                composed.clip,
                request.output_path,
                config,
                work_dir,
                reporter,
            )

            lifecycle.transition(RenderPhase.FINALIZING)
            reporter.report(RenderPhase.FINALIZING, 96, "Finalizing output…")
            promote_partial_output(request.output_path)

            metadata = build_output_metadata(request.output_path, config)
            if request.metadata_path:
                write_render_output_artifact(metadata, request.metadata_path)

            lifecycle.transition(RenderPhase.COMPLETED)
            lifecycle.clear_state()
            reporter.report(RenderPhase.COMPLETED, 100, "Render complete")

            logger.info(
                "Rendered video -> %s (%.1fs, %d bytes, attempt %d)",
                request.output_path,
                metadata.duration_seconds,
                metadata.file_size_bytes,
                attempt,
            )
            return str(request.output_path.resolve()), metadata

        except RenderingError:
            raise
        except Exception as exc:
            lifecycle.transition(RenderPhase.FAILED, error=str(exc))
            remove_partial_output(request.output_path)
            raise RenderingError(
                str(exc),
                attempt=attempt,
                phase=lifecycle.phase.value,
                cause=str(exc),
            ) from exc
        finally:
            resources.close_all()
            cleanup_render_temp(work_dir)
