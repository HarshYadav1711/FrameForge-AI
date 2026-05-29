"""Video rendering engine (MoviePy + FFmpeg)."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.models.schemas import Scene, TranscriptSegment, VisualTimeline
from app.services.rendering.config import RenderOutputConfig, render_config_from_settings
from app.services.rendering.engine import VideoRenderEngine
from app.services.rendering.formats import read_render_output_artifact, write_render_output_artifact
from app.services.rendering.lifecycle import RenderLifecycle, pipeline_percent_from_render
from app.services.rendering.metadata import build_output_metadata
from app.models.schemas import RenderingProgress
from app.services.rendering.progress import ProgressCallback
from app.services.rendering.queue import RenderQueue, get_render_queue
from app.services.rendering.request import RenderRequest

__all__ = [
    "RenderLifecycle",
    "RenderOutputConfig",
    "RenderQueue",
    "RenderRequest",
    "RenderingProgress",
    "VideoRenderEngine",
    "build_output_metadata",
    "get_render_queue",
    "pipeline_percent_from_render",
    "read_render_output_artifact",
    "render_config_from_settings",
    "render_video",
    "write_render_output_artifact",
]


def render_video(
    scenes: list[Scene],
    audio_path: Path,
    output_path: Path,
    settings: Settings,
    *,
    srt_path: Path | None = None,
    transcript_segments: list[TranscriptSegment] | None = None,
    visual_timeline: VisualTimeline | None = None,
    on_progress: ProgressCallback | None = None,
    job_id: str | None = None,
    metadata_path: Path | None = None,
    state_path: Path | None = None,
) -> str:
    """
    Compose scene visuals, subtitles, and narration into an optimized MP4.

    Returns the output file path. Use ``on_progress`` for encode tracking.
    """
    request = RenderRequest(
        scenes=scenes,
        audio_path=audio_path,
        output_path=output_path,
        settings=settings,
        srt_path=srt_path,
        transcript_segments=transcript_segments,
        visual_timeline=visual_timeline,
        job_id=job_id,
        metadata_path=metadata_path,
        state_path=state_path,
        work_dir=output_path.parent / settings.render_temp_subdir,
    )
    path, _metadata = VideoRenderEngine(settings).render(request, on_progress=on_progress)
    return path
