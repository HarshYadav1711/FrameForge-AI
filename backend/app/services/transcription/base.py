"""Transcription service abstraction and shared result types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.models.schemas import (
    SubtitleCue,
    TranscriptSegment,
    TranscriptionMetadata,
    TranscriptionProgress,
    TranscriptResult,
    TranscriptTimelineBlock,
)

ProgressCallback = Callable[[TranscriptionProgress], None]


@dataclass(frozen=True)
class TranscriptionRequest:
    """Input for a transcription run."""

    audio_path: Path
    language: str | None = None
    initial_prompt: str | None = None


@runtime_checkable
class TranscriptionService(Protocol):
    """Pluggable local transcription backend."""

    def transcribe(
        self,
        request: TranscriptionRequest,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> TranscriptResult:
        """Transcribe audio and return a structured, timeline-ready result."""
        ...


def segments_to_subtitle_cues(
    segments: list[TranscriptSegment],
) -> list[SubtitleCue]:
    """Build numbered subtitle cues from transcript segments."""
    cues: list[SubtitleCue] = []
    index = 1
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        cues.append(
            SubtitleCue(
                index=index,
                start=seg.start,
                end=seg.end,
                text=text,
            )
        )
        index += 1
    return cues


def build_timeline_blocks(
    segments: list[TranscriptSegment],
    *,
    max_block_duration: float = 30.0,
    max_block_chars: int = 500,
) -> list[TranscriptTimelineBlock]:
    """
    Merge adjacent segments into timeline blocks for scene segmentation
    and synchronization.
    """
    if not segments:
        return []

    blocks: list[TranscriptTimelineBlock] = []
    block_index = 0
    chunk_start = segments[0].start
    chunk_end = segments[0].end
    chunk_texts: list[str] = [segments[0].text.strip()]

    def flush() -> None:
        nonlocal block_index, chunk_start, chunk_end, chunk_texts
        text = " ".join(t for t in chunk_texts if t).strip()
        if text:
            blocks.append(
                TranscriptTimelineBlock(
                    index=block_index,
                    start=round(chunk_start, 3),
                    end=round(chunk_end, 3),
                    text=text,
                )
            )
            block_index += 1
        chunk_texts = []

    for seg in segments[1:]:
        text = seg.text.strip()
        duration = seg.end - chunk_start
        combined_len = sum(len(t) for t in chunk_texts) + len(text)

        if duration > max_block_duration or combined_len > max_block_chars:
            flush()
            chunk_start = seg.start
            chunk_end = seg.end
            chunk_texts = [text] if text else []
        else:
            chunk_end = seg.end
            if text:
                chunk_texts.append(text)

    if chunk_texts:
        flush()

    return blocks


def build_transcript_result(
    segments: list[TranscriptSegment],
    metadata: TranscriptionMetadata,
    *,
    max_block_duration: float = 30.0,
) -> TranscriptResult:
    """Assemble a full transcript result with derived timeline and subtitle data."""
    return TranscriptResult(
        segments=segments,
        timeline_blocks=build_timeline_blocks(
            segments,
            max_block_duration=max_block_duration,
        ),
        subtitle_cues=segments_to_subtitle_cues(segments),
        metadata=metadata,
    )
