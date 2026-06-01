"""Tests for scene-based subtitles and segmentation text sources."""

from __future__ import annotations

from app.models.schemas import Scene, SubtitleCue, TranscriptTimelineBlock
from app.services.segmentation.base import SegmentationContext
from app.services.segmentation.heuristic import propose_heuristic
from app.config import Settings
from app.services.subtitles.utils import cues_from_scenes
import asyncio


async def _heuristic(script: str, blocks: list[TranscriptTimelineBlock]) -> list:
    ctx = SegmentationContext(
        script=script,
        segments=[],
        timeline_blocks=blocks,
        total_duration=30.0,
        settings=Settings(),
    )
    return await propose_heuristic(ctx)


def test_heuristic_prefers_script_over_whisper_blocks() -> None:
    script = "When you check a message, open a browser tab, and answer an email."
    blocks = [
        TranscriptTimelineBlock(
            index=0,
            start=0.0,
            end=30.0,
            text="SeoShineVimbContentOff garbage whisper output",
        )
    ]
    drafts = asyncio.run(_heuristic(script, blocks))
    assert drafts
    assert "message" in drafts[0].narration.lower()
    assert "SeoShine" not in drafts[0].narration


def test_cues_from_scenes_use_narration() -> None:
    scenes = [
        Scene(
            index=0,
            title="Intro",
            narration="Hello world",
            visual_prompt="bg",
            start_time=0.0,
            end_time=2.0,
        )
    ]
    cues = cues_from_scenes(scenes)
    assert len(cues) == 1
    assert cues[0].text == "Hello world"
