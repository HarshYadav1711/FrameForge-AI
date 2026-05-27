"""Configurable scene duration constraints (split / merge)."""

from __future__ import annotations

import logging
import re

from app.config import Settings
from app.models.schemas import Scene, SceneMetadata

logger = logging.getLogger(__name__)


def _scene_duration(scene: Scene) -> float:
    if scene.start_time is None or scene.end_time is None:
        return 0.0
    return max(0.0, scene.end_time - scene.start_time)


def apply_duration_constraints(
    scenes: list[Scene],
    settings: Settings,
) -> list[Scene]:
    """Merge scenes shorter than min duration; split scenes longer than max."""
    if not scenes:
        return scenes

    min_dur = settings.scene_min_duration_seconds
    max_dur = settings.scene_max_duration_seconds

    merged = _merge_short_scenes(scenes, min_dur)
    split = _split_long_scenes(merged, max_dur)
    return split


def _merge_short_scenes(scenes: list[Scene], min_duration: float) -> list[Scene]:
    if len(scenes) <= 1 or min_duration <= 0:
        return scenes

    merged: list[Scene] = []
    buffer: Scene | None = None

    for scene in scenes:
        if buffer is None:
            buffer = scene
            continue

        buffer_dur = _scene_duration(buffer)
        scene_dur = _scene_duration(scene)

        if buffer_dur < min_duration or scene_dur < min_duration:
            buffer = _combine_scenes(buffer, scene)
        else:
            merged.append(buffer)
            buffer = scene

    if buffer is not None:
        merged.append(buffer)

    return merged


def _combine_scenes(a: Scene, b: Scene) -> Scene:
    meta = a.metadata or SceneMetadata()
    end = b.end_time if b.end_time is not None else a.end_time
    return a.model_copy(
        update={
            "title": a.title,
            "narration": f"{a.narration.strip()} {b.narration.strip()}".strip(),
            "visual_prompt": a.visual_prompt,
            "start_time": a.start_time,
            "end_time": end,
            "metadata": meta.model_copy(
                update={
                    "semantic_group": meta.semantic_group or "merged",
                }
            ),
        }
    )


def _split_long_scenes(scenes: list[Scene], max_duration: float) -> list[Scene]:
    if max_duration <= 0:
        return scenes

    result: list[Scene] = []
    for scene in scenes:
        duration = _scene_duration(scene)
        if duration <= max_duration or not scene.narration.strip():
            result.append(scene)
            continue

        parts = _split_narration_at_sentences(scene.narration)
        if len(parts) <= 1:
            result.append(scene)
            continue

        start = scene.start_time or 0.0
        end = scene.end_time or start + duration
        total_words = sum(max(len(p.split()), 1) for p in parts)
        cursor = start

        for i, part in enumerate(parts):
            weight = max(len(part.split()), 1) / total_words
            part_end = end if i == len(parts) - 1 else min(cursor + duration * weight, end)
            meta = scene.metadata or SceneMetadata()
            result.append(
                scene.model_copy(
                    update={
                        "title": part[:48].rstrip() + ("…" if len(part) > 48 else ""),
                        "narration": part.strip(),
                        "start_time": round(cursor, 3),
                        "end_time": round(part_end, 3),
                        "metadata": meta.model_copy(
                            update={"semantic_group": f"{meta.semantic_group or 'scene'}_part"}
                        ),
                    }
                )
            )
            cursor = part_end

    return result


def _split_narration_at_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(parts) <= 1:
        return [text]

    chunks: list[str] = []
    buf: list[str] = []
    for part in parts:
        buf.append(part)
        if len(buf) >= 2:
            chunks.append(" ".join(buf))
            buf = []
    if buf:
        chunks.append(" ".join(buf))
    return chunks
