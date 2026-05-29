"""Visual timeline generation from segmented scenes."""

from __future__ import annotations

import logging

from app.config import Settings
from app.models.schemas import (
    MediaType,
    Scene,
    TransitionType,
    VisualAssemblyMetadata,
    VisualTimeline,
    VisualTimelineEntry,
)

logger = logging.getLogger(__name__)


def _resolve_transition(scene: Scene, settings: Settings) -> tuple[TransitionType, float]:
    visual = scene.metadata.visual if scene.metadata else None
    if visual:
        return visual.transition_in, visual.transition_duration_seconds

    name = settings.visual_default_transition.lower()
    try:
        transition = TransitionType(name)
    except ValueError:
        transition = TransitionType.FADE

    duration = settings.visual_transition_seconds
    if transition == TransitionType.CROSSFADE:
        duration = settings.visual_crossfade_seconds
    return transition, duration


def _render_path(scene: Scene) -> str | None:
    visual = scene.metadata.visual if scene.metadata else None
    if visual and visual.normalized_path:
        return visual.normalized_path
    return scene.image_path


def _media_type(scene: Scene) -> MediaType:
    if scene.metadata and scene.metadata.visual:
        return scene.metadata.visual.media_type
    return MediaType.GENERATED if scene.image_path else MediaType.IMAGE


def build_visual_timeline(
    scenes: list[Scene],
    total_duration: float,
    settings: Settings,
) -> VisualTimeline:
    """Build a contiguous visual timeline aligned to scene timestamps."""
    entries: list[VisualTimelineEntry] = []
    transitions_applied = 0

    for scene in scenes:
        media_path = _render_path(scene)
        if not media_path:
            continue

        start = scene.start_time if scene.start_time is not None else 0.0
        end = scene.end_time if scene.end_time is not None else total_duration
        duration = max(end - start, settings.visual_min_scene_seconds)

        transition_in, transition_duration = _resolve_transition(scene, settings)
        if transition_in != TransitionType.CUT:
            transitions_applied += 1

        entries.append(
            VisualTimelineEntry(
                scene_index=scene.index,
                start=round(start, 3),
                end=round(start + duration, 3),
                duration=round(duration, 3),
                media_path=media_path,
                media_type=_media_type(scene),
                transition_in=transition_in,
                transition_duration_seconds=transition_duration,
            )
        )

    if entries and total_duration > 0:
        last = entries[-1]
        end_cap = round(total_duration, 3)
        if last.end < end_cap:
            entries[-1] = last.model_copy(
                update={
                    "end": end_cap,
                    "duration": round(end_cap - last.start, 3),
                }
            )

    normalized_assets = sum(
        1
        for s in scenes
        if s.metadata
        and s.metadata.visual
        and s.metadata.visual.normalized_path
    )

    timeline = VisualTimeline(
        entries=entries,
        metadata=VisualAssemblyMetadata(
            entry_count=len(entries),
            total_duration_seconds=round(total_duration, 3),
            transitions_applied=transitions_applied,
            normalized_assets=normalized_assets,
        ),
    )
    logger.info(
        "Built visual timeline: %d entries, %.1fs total",
        len(entries),
        total_duration,
    )
    return timeline
