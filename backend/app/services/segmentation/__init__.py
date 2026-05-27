"""Scene segmentation pipeline."""

from __future__ import annotations

import logging

from app.config import Settings
from app.core.exceptions import SegmentationError
from app.models.schemas import (
    Scene,
    SegmentationResult,
    TranscriptSegment,
    TranscriptTimelineBlock,
)
from app.services.segmentation.base import SegmentationContext
from app.services.segmentation.formats import read_scenes_artifact, write_scenes_artifact
from app.services.segmentation.pipeline import SceneSegmentationPipeline

logger = logging.getLogger(__name__)

__all__ = [
    "SceneSegmentationPipeline",
    "read_scenes_artifact",
    "segment_script",
    "write_scenes_artifact",
]


async def segment_script(
    script: str,
    segments: list[TranscriptSegment],
    total_duration: float,
    settings: Settings,
    *,
    timeline_blocks: list[TranscriptTimelineBlock] | None = None,
    scenes_out=None,
) -> list[Scene]:
    """
    Split narration into timeline-aware scenes (pipeline entry point).

    Returns scenes for backward compatibility with the video orchestrator.
    """
    ctx = SegmentationContext(
        script=script,
        segments=segments,
        timeline_blocks=timeline_blocks or [],
        total_duration=total_duration,
        settings=settings,
    )

    pipeline = SceneSegmentationPipeline(settings)

    try:
        result = await pipeline.run(ctx)
    except SegmentationError:
        raise
    except Exception as exc:
        logger.exception("Unexpected segmentation failure")
        raise SegmentationError(
            "Unexpected segmentation error",
            cause=str(exc),
        ) from exc

    if scenes_out is not None:
        write_scenes_artifact(result, scenes_out)

    logger.info(
        "Segmented into %d scenes (source=%s, timeline_aligned=%s)",
        len(result.scenes),
        result.metadata.source,
        result.metadata.timeline_aligned,
    )
    return result.scenes


async def segment_script_full(
    script: str,
    segments: list[TranscriptSegment],
    total_duration: float,
    settings: Settings,
    *,
    timeline_blocks: list[TranscriptTimelineBlock] | None = None,
    scenes_out=None,
) -> SegmentationResult:
    """Segment and return the full structured result."""
    scenes = await segment_script(
        script,
        segments,
        total_duration,
        settings,
        timeline_blocks=timeline_blocks,
        scenes_out=scenes_out,
    )
    if scenes_out and scenes_out.exists():
        return read_scenes_artifact(scenes_out)

    from app.services.segmentation.base import build_segmentation_result

    return build_segmentation_result(
        scenes,
        source="unknown",
        total_duration=total_duration,
    )
