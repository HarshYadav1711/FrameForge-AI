"""Tests for scene timestamp alignment edge cases."""

from __future__ import annotations

import asyncio

import pytest

from app.config import Settings
from app.models.schemas import TranscriptSegment, TranscriptTimelineBlock
from app.services.segmentation import segment_script
from app.services.segmentation.base import SceneDraft
from app.services.segmentation.timeline import apply_timestamps


def test_many_drafts_few_segments_does_not_crash() -> None:
    """LLM-style multi-scene output with a single Whisper segment must not IndexError."""
    segments = [
        TranscriptSegment(start=0.0, end=30.0, text="Full narration for the entire clip."),
    ]
    drafts = [
        SceneDraft(
            title=f"Scene {i}",
            narration=f"Scene {i} has its own narration chunk.",
            visual_prompt="Cinematic background",
            semantic_group=f"llm_scene_{i}",
        )
        for i in range(5)
    ]

    timed = apply_timestamps(drafts, segments, 30.0)

    assert len(timed) == 5
    assert timed[0][1] == 0.0
    assert timed[-1][2] == 30.0
    for i in range(len(timed) - 1):
        assert timed[i][2] <= timed[i + 1][1] + 0.001


def test_overlapping_windows_split_by_word_weight() -> None:
    segments = [TranscriptSegment(start=0.0, end=10.0, text="one two three four five")]
    drafts = [
        SceneDraft(title="A", narration="short", visual_prompt="v", semantic_group="a"),
        SceneDraft(
            title="B",
            narration="much longer narration chunk here",
            visual_prompt="v",
            semantic_group="b",
        ),
    ]

    timed = apply_timestamps(drafts, segments, 10.0)

    assert len(timed) == 2
    assert timed[0][1] == 0.0
    assert timed[1][2] == 10.0
    assert timed[0][2] < timed[1][1] or timed[0][2] == timed[1][1]


@pytest.mark.asyncio
async def test_segment_script_auto_with_segment_mismatch() -> None:
    settings = Settings(ollama_enabled=False, segmentation_backend="heuristic")
    script = "First scene words. Second scene words. Third scene words. Fourth scene words."
    segments = [TranscriptSegment(start=0.0, end=12.0, text=script)]
    blocks = [TranscriptTimelineBlock(index=0, start=0.0, end=12.0, text=script)]

    scenes = await segment_script(
        script,
        segments,
        12.0,
        settings,
        timeline_blocks=blocks,
    )

    assert len(scenes) >= 1
    assert scenes[-1].end_time == 12.0
