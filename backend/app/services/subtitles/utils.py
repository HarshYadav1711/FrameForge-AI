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

# Common LaTeX tokens from scripts — replaced for readable burned-in subtitles.
_LATEX_TOKEN_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\displaystyle", " "),
    (r"\partial", "∂"),
    (r"\infty", "∞"),
    (r"\alpha", "α"),
    (r"\beta", "β"),
    (r"\gamma", "γ"),
    (r"\Delta", "Δ"),
    (r"\sum", "Σ"),
    (r"\int", "∫"),
)

_LATEX_COMMAND_RE = re.compile(r"\\[a-zA-Z]+")
_LATEX_BRACES_RE = re.compile(r"[{}$]")
_WHITESPACE_RE = re.compile(r"\s+")


def sanitize_display_text(text: str) -> str:
    """Make script/transcript text readable in burned-in subtitles."""
    cleaned = text.strip()
    for token, replacement in _LATEX_TOKEN_REPLACEMENTS:
        cleaned = cleaned.replace(token, replacement)
    cleaned = _LATEX_COMMAND_RE.sub(" ", cleaned)
    cleaned = _LATEX_BRACES_RE.sub(" ", cleaned)
    return _WHITESPACE_RE.sub(" ", cleaned).strip()


def chunk_cues_for_display(
    cues: list[SubtitleCue],
    *,
    max_chars: int = 84,
    max_duration: float = 5.0,
) -> list[SubtitleCue]:
    """
    Split long cues into short, readable on-screen chunks.

    Prevents a single transcript segment from filling the frame with wrapped text.
    """
    if not cues:
        return []

    chunked: list[SubtitleCue] = []
    next_index = 1

    for cue in cues:
        text = sanitize_display_text(cue.text)
        span = max(cue.end - cue.start, 0.05)
        if not text:
            continue

        if len(text) <= max_chars and span <= max_duration:
            chunked.append(
                cue.model_copy(
                    update={"index": next_index, "text": text},
                )
            )
            next_index += 1
            continue

        parts = _split_text_for_cues(text, max_chars=max_chars)
        if not parts:
            continue

        total_weight = sum(max(len(part), 1) for part in parts)
        cursor = cue.start

        for i, part in enumerate(parts):
            weight = max(len(part), 1) / total_weight
            part_end = cue.end if i == len(parts) - 1 else min(
                cursor + span * weight,
                cue.end,
            )
            chunked.append(
                SubtitleCue(
                    index=next_index,
                    start=round(cursor, 3),
                    end=round(part_end, 3),
                    text=part,
                )
            )
            next_index += 1
            cursor = part_end

    return normalize_cues(chunked)


def _split_text_for_cues(text: str, *, max_chars: int) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        sentences = [text]

    parts: list[str] = []
    buffer = ""

    def flush() -> None:
        nonlocal buffer
        if buffer.strip():
            parts.append(buffer.strip())
        buffer = ""

    for sentence in sentences:
        if len(sentence) <= max_chars:
            candidate = f"{buffer} {sentence}".strip() if buffer else sentence
            if len(candidate) <= max_chars:
                buffer = candidate
            else:
                flush()
                buffer = sentence
        else:
            flush()
            words = sentence.split()
            word_buf: list[str] = []
            for word in words:
                candidate = " ".join(word_buf + [word])
                if len(candidate) <= max_chars or not word_buf:
                    word_buf.append(word)
                else:
                    parts.append(" ".join(word_buf))
                    word_buf = [word]
            if word_buf:
                parts.append(" ".join(word_buf))

    flush()
    return parts


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
