"""SRT file generation."""

from __future__ import annotations

import logging
from pathlib import Path

from app.models.schemas import SubtitleCue, TranscriptSegment
from app.services.subtitles.utils import build_srt_content, cues_from_segments, normalize_cues

logger = logging.getLogger(__name__)


def generate_srt(
    segments: list[TranscriptSegment],
    output_path: Path,
) -> str:
    """Write SRT subtitles from transcript segments."""
    cues = normalize_cues(cues_from_segments(segments))
    content = build_srt_content(cues)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info("Wrote subtitles %s (%d cues)", output_path.name, len(cues))
    return str(output_path)


def generate_srt_from_cues(
    cues: list[SubtitleCue],
    output_path: Path,
) -> str:
    """Write SRT from pre-built subtitle cues."""
    content = build_srt_content(normalize_cues(cues))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info("Wrote subtitles %s (%d cues)", output_path.name, len(cues))
    return str(output_path)
