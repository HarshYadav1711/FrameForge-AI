"""Transcription pipeline — local Faster-Whisper with structured outputs."""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import Settings
from app.core.exceptions import TranscriptionError
from app.models.schemas import (
    TranscriptSegment,
    TranscriptionProgress,
    TranscriptResult,
)
from app.services.transcription.base import (
    ProgressCallback,
    TranscriptionRequest,
    TranscriptionService,
    build_transcript_result,
    build_timeline_blocks,
    segments_to_subtitle_cues,
)
from app.services.transcription.formats import read_transcript_artifact, write_transcript_artifact
from app.services.transcription.faster_whisper import (
    FasterWhisperTranscriptionService,
    get_faster_whisper_service,
)

logger = logging.getLogger(__name__)

__all__ = [
    "FasterWhisperTranscriptionService",
    "ProgressCallback",
    "TranscriptionService",
    "build_timeline_blocks",
    "get_transcription_service",
    "read_transcript_artifact",
    "segments_to_subtitle_cues",
    "transcribe_audio",
    "write_transcript_artifact",
]


def get_transcription_service(settings: Settings) -> TranscriptionService:
    """Factory for the configured transcription backend."""
    backend = settings.transcription_backend.lower().strip()
    if backend in ("faster_whisper", "faster-whisper", "whisper"):
        return get_faster_whisper_service(settings)
    raise TranscriptionError(
        f"Unsupported transcription backend: {backend}",
        cause="invalid_backend",
    )


def transcribe_audio(
    audio_path: Path,
    settings: Settings,
    *,
    transcript_out: Path | None = None,
    language: str | None = None,
    initial_prompt: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> tuple[list[TranscriptSegment], float]:
    """
    Transcribe narration audio (pipeline entry point).

    Returns segments and duration for backward compatibility with the orchestrator.
    """
    service = get_transcription_service(settings)
    request = TranscriptionRequest(
        audio_path=audio_path,
        language=language,
        initial_prompt=initial_prompt,
    )

    try:
        result = service.transcribe(request, on_progress=on_progress)
    except TranscriptionError:
        raise
    except Exception as exc:
        logger.exception("Unexpected transcription failure")
        raise TranscriptionError(
            "Unexpected transcription error",
            cause=str(exc),
        ) from exc

    if transcript_out is not None:
        write_transcript_artifact(result, transcript_out)

    duration = result.metadata.duration_seconds
    return result.segments, duration


def transcribe_audio_full(
    audio_path: Path,
    settings: Settings,
    *,
    transcript_out: Path | None = None,
    language: str | None = None,
    initial_prompt: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> TranscriptResult:
    """Transcribe and return the full structured result."""
    service = get_transcription_service(settings)
    request = TranscriptionRequest(
        audio_path=audio_path,
        language=language,
        initial_prompt=initial_prompt,
    )
    try:
        result = service.transcribe(request, on_progress=on_progress)
    except TranscriptionError:
        raise
    except Exception as exc:
        logger.exception("Unexpected transcription failure")
        raise TranscriptionError(
            "Unexpected transcription error",
            cause=str(exc),
        ) from exc

    if transcript_out is not None:
        write_transcript_artifact(result, transcript_out)
    return result
