"""Scene segmentation types and shared builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.config import Settings
from app.models.schemas import (
    Scene,
    SceneMetadata,
    SegmentationMetadata,
    SegmentationResult,
    TranscriptSegment,
    TranscriptTimelineBlock,
)


@dataclass
class SceneDraft:
    """Intermediate scene before timeline alignment and indexing."""

    title: str
    narration: str
    visual_prompt: str
    semantic_group: str | None = None
    transcript_segment_start: int | None = None
    transcript_segment_end: int | None = None


@dataclass
class SegmentationContext:
    """Input context for the segmentation pipeline."""

    script: str
    segments: list[TranscriptSegment]
    timeline_blocks: list[TranscriptTimelineBlock]
    total_duration: float
    settings: Settings


@runtime_checkable
class SceneProposer(Protocol):
    """Produces raw scene drafts (LLM, timeline, or heuristic)."""

    async def propose(self, ctx: SegmentationContext) -> list[SceneDraft]:
        ...


def _scene_duration(scene: Scene) -> float:
    if scene.start_time is None or scene.end_time is None:
        return 0.0
    return max(0.0, scene.end_time - scene.start_time)


def finalize_scenes(
    scenes: list[Scene],
    *,
    source: str,
) -> list[Scene]:
    """Assign stable indices and populate scene metadata."""
    finalized: list[Scene] = []
    for index, scene in enumerate(scenes):
        duration = _scene_duration(scene)
        word_count = len(scene.narration.split())
        meta = scene.metadata or SceneMetadata()
        finalized.append(
            scene.model_copy(
                update={
                    "index": index,
                    "metadata": meta.model_copy(
                        update={
                            "source": meta.source or source,
                            "word_count": word_count,
                            "duration_seconds": round(duration, 3) if duration else None,
                        }
                    ),
                }
            )
        )
    return finalized


def build_segmentation_result(
    scenes: list[Scene],
    *,
    source: str,
    total_duration: float,
) -> SegmentationResult:
    indexed = finalize_scenes(scenes, source=source)
    return SegmentationResult(
        scenes=indexed,
        metadata=SegmentationMetadata(
            scene_count=len(indexed),
            total_duration_seconds=round(total_duration, 3),
            source=source,
            timeline_aligned=any(s.start_time is not None for s in indexed),
        ),
    )
