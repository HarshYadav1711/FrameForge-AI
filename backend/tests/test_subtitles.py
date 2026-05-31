"""Tests for subtitle cue preparation and display sanitization."""

from __future__ import annotations

from app.models.schemas import SubtitleCue
from app.services.subtitles.utils import (
    chunk_cues_for_display,
    sanitize_display_text,
)


def test_sanitize_display_text_strips_latex_commands() -> None:
    text = r"\displaystyle f(x)=\partial x + \alpha"
    cleaned = sanitize_display_text(text)
    assert r"\displaystyle" not in cleaned
    assert r"\partial" not in cleaned
    assert "∂" in cleaned
    assert "α" in cleaned


def test_chunk_cues_splits_long_segment() -> None:
    long_text = " ".join(["word"] * 40)
    cues = [
        SubtitleCue(index=1, start=0.0, end=20.0, text=long_text),
    ]

    chunked = chunk_cues_for_display(cues, max_chars=40, max_duration=5.0)

    assert len(chunked) > 1
    assert chunked[0].start == 0.0
    assert chunked[-1].end == 20.0
    assert all(len(c.text) <= 40 for c in chunked)
