"""Subtitle utilities — cues, SRT, and timeline helpers."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from app.models.schemas import SubtitleCue, TranscriptSegment

logger = logging.getLogger(__name__)

_SRT_TIMESTAMP = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)


def format_srt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    if ms >= 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt_timestamp(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def cues_from_segments(segments: list[TranscriptSegment]) -> list[SubtitleCue]:
    cues: list[SubtitleCue] = []
    index = 1
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        cues.append(
            SubtitleCue(
                index=index,
                start=round(seg.start, 3),
                end=round(seg.end, 3),
                text=text,
            )
        )
        index += 1
    return cues


def normalize_cues(cues: list[SubtitleCue], min_duration: float = 0.05) -> list[SubtitleCue]:
    """Ensure monotonic timeline and minimum on-screen duration."""
    if not cues:
        return []

    sorted_cues = sorted(cues, key=lambda c: c.start)
    normalized: list[SubtitleCue] = []

    for i, cue in enumerate(sorted_cues):
        start = max(0.0, cue.start)
        end = max(start + min_duration, cue.end)
        if normalized and start < normalized[-1].end:
            start = normalized[-1].end
            end = max(end, start + min_duration)
        normalized.append(
            cue.model_copy(
                update={
                    "index": i + 1,
                    "start": round(start, 3),
                    "end": round(end, 3),
                }
            )
        )

    return normalized


def build_srt_content(cues: list[SubtitleCue]) -> str:
    lines: list[str] = []
    for cue in cues:
        if not cue.text.strip():
            continue
        lines.append(str(cue.index))
        lines.append(
            f"{format_srt_timestamp(cue.start)} --> {format_srt_timestamp(cue.end)}"
        )
        lines.append(cue.text.strip())
        lines.append("")
    return "\n".join(lines)


def parse_srt_file(path: Path) -> list[SubtitleCue]:
    """Parse an SRT file into subtitle cues."""
    content = path.read_text(encoding="utf-8")
    return parse_srt_content(content)


def parse_srt_content(content: str) -> list[SubtitleCue]:
    cues: list[SubtitleCue] = []
    blocks = re.split(r"\n\s*\n", content.strip())
    index = 1

    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue

        time_line_idx = 0
        if lines[0].isdigit():
            time_line_idx = 1
        if time_line_idx >= len(lines):
            continue

        match = _SRT_TIMESTAMP.match(lines[time_line_idx])
        if not match:
            continue

        start = parse_srt_timestamp(*match.groups()[:4])
        end = parse_srt_timestamp(*match.groups()[4:8])
        text = "\n".join(lines[time_line_idx + 1 :]).strip()
        if not text:
            continue

        cues.append(
            SubtitleCue(
                index=index,
                start=round(start, 3),
                end=round(end, 3),
                text=text,
            )
        )
        index += 1

    return normalize_cues(cues)


def cue_duration(cue: SubtitleCue) -> float:
    return max(0.0, cue.end - cue.start)
