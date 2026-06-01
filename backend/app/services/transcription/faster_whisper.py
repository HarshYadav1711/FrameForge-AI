"""Faster-Whisper implementation of the transcription service."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from app.config import Settings
from app.core.exceptions import TranscriptionError
from app.models.schemas import (
    TranscriptSegment,
    TranscriptWord,
    TranscriptionMetadata,
    TranscriptionProgress,
    TranscriptResult,
)
from app.services.transcription.base import (
    ProgressCallback,
    TranscriptionRequest,
    TranscriptionService,
    build_transcript_result,
)

logger = logging.getLogger(__name__)

_model_lock = threading.Lock()
_whisper_model = None
_model_config_key: tuple[str, str, str] | None = None

_CPU_COMPUTE_TYPE = "int8"


def _is_gpu_runtime_error(exc: BaseException) -> bool:
    """True when CUDA/cuBLAS libraries are missing or GPU init failed."""
    message = f"{exc}".lower()
    markers = (
        "cublas",
        "cudnn",
        "cudart",
        "cuda",
        "gpu",
        "dll is not found",
        "cannot be loaded",
        "no cuda",
    )
    return any(marker in message for marker in markers)


def _uses_gpu(device: str) -> bool:
    return device.strip().lower() in ("cuda", "gpu", "auto")


def _reset_model_cache() -> None:
    global _whisper_model, _model_config_key
    with _model_lock:
        _whisper_model = None
        _model_config_key = None


def _cpu_fallback_settings(settings: Settings) -> Settings:
    compute = settings.whisper_compute_type
    if compute in ("float16", "float32", "default"):
        compute = _CPU_COMPUTE_TYPE
    return settings.model_copy(
        update={
            "whisper_device": "cpu",
            "whisper_compute_type": compute,
        }
    )


def _load_model(settings: Settings):
    """Lazy-load WhisperModel with thread-safe singleton keyed by config."""
    global _whisper_model, _model_config_key

    key = (
        settings.whisper_model,
        settings.whisper_device,
        settings.whisper_compute_type,
    )

    with _model_lock:
        if _whisper_model is not None and _model_config_key == key:
            return _whisper_model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionError(
                "faster-whisper is not installed",
                cause="import_error",
            ) from exc

        logger.info(
            "Loading Whisper model=%s device=%s compute_type=%s",
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type,
        )
        try:
            model = WhisperModel(
                settings.whisper_model,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
        except Exception as exc:
            logger.exception("Failed to load Whisper model")
            raise TranscriptionError(
                f"Could not load Whisper model '{settings.whisper_model}'",
                cause=str(exc),
            ) from exc

        _whisper_model = model
        _model_config_key = key
        logger.info("Whisper model ready")
        return _whisper_model


def _load_model_resilient(settings: Settings) -> tuple[object, Settings]:
    """Load Whisper on the requested device, falling back to CPU when GPU libs are missing."""
    try:
        return _load_model(settings), settings
    except TranscriptionError as exc:
        root = exc.__cause__ if exc.__cause__ is not None else exc
        if not _uses_gpu(settings.whisper_device) or not _is_gpu_runtime_error(root):
            raise
        logger.warning(
            "GPU transcription unavailable (%s); falling back to CPU",
            root,
        )
        _reset_model_cache()
        cpu_settings = _cpu_fallback_settings(settings)
        return _load_model(cpu_settings), cpu_settings
    except Exception as exc:
        if not _uses_gpu(settings.whisper_device) or not _is_gpu_runtime_error(exc):
            raise
        logger.warning(
            "GPU transcription unavailable (%s); falling back to CPU",
            exc,
        )
        _reset_model_cache()
        cpu_settings = _cpu_fallback_settings(settings)
        return _load_model(cpu_settings), cpu_settings


def _emit_progress(
    callback: ProgressCallback | None,
    *,
    phase: str,
    percent: int,
    message: str,
    segments_completed: int = 0,
) -> None:
    if callback is None:
        return
    try:
        callback(
            TranscriptionProgress(
                phase=phase,
                percent=min(100, max(0, percent)),
                message=message,
                segments_completed=segments_completed,
            )
        )
    except Exception:
        logger.warning("Transcription progress callback failed", exc_info=True)


class FasterWhisperTranscriptionService:
    """Local Faster-Whisper transcription backend."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def transcribe(
        self,
        request: TranscriptionRequest,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> TranscriptResult:
        audio_path = request.audio_path
        if not audio_path.is_file():
            raise TranscriptionError(
                f"Audio file not found: {audio_path}",
                cause="file_not_found",
            )

        _emit_progress(
            on_progress,
            phase="loading_model",
            percent=5,
            message="Loading transcription model…",
        )

        model, settings = _load_model_resilient(self._settings)

        transcribe_kwargs: dict = {
            "vad_filter": settings.whisper_vad_filter,
            "word_timestamps": settings.whisper_word_timestamps,
            "beam_size": settings.whisper_beam_size,
        }
        language = request.language or settings.whisper_language
        if language:
            transcribe_kwargs["language"] = language

        prompt = request.initial_prompt or settings.whisper_initial_prompt
        if prompt:
            transcribe_kwargs["initial_prompt"] = prompt

        _emit_progress(
            on_progress,
            phase="transcribing",
            percent=10,
            message="Transcribing audio…",
        )

        try:
            segments_iter, info = model.transcribe(
                str(audio_path),
                **transcribe_kwargs,
            )
        except Exception as exc:
            if _uses_gpu(settings.whisper_device) and _is_gpu_runtime_error(exc):
                logger.warning(
                    "GPU transcribe failed (%s); retrying on CPU",
                    exc,
                )
                _reset_model_cache()
                cpu_settings = _cpu_fallback_settings(self._settings)
                model, settings = _load_model_resilient(cpu_settings)
                segments_iter, info = model.transcribe(
                    str(audio_path),
                    **transcribe_kwargs,
                )
            else:
                logger.exception("Transcription failed for %s", audio_path.name)
                raise TranscriptionError(
                    "Audio transcription failed",
                    cause=str(exc),
                ) from exc

        total_duration = float(info.duration) if info.duration else 0.0
        detected_language = getattr(info, "language", None)
        language_probability = getattr(info, "language_probability", None)

        segments: list[TranscriptSegment] = []
        segment_count = 0

        try:
            for raw in segments_iter:
                segment_count += 1
                words: list[TranscriptWord] | None = None
                if settings.whisper_word_timestamps and raw.words:
                    words = [
                        TranscriptWord(
                            start=round(w.start, 3),
                            end=round(w.end, 3),
                            word=w.word.strip(),
                        )
                        for w in raw.words
                        if w.word.strip()
                    ]

                segments.append(
                    TranscriptSegment(
                        start=round(raw.start, 3),
                        end=round(raw.end, 3),
                        text=raw.text.strip(),
                        confidence=(
                            round(logprob, 4)
                            if (logprob := getattr(raw, "avg_logprob", None))
                            is not None
                            else None
                        ),
                        words=words,
                    )
                )

                if total_duration > 0:
                    pct = 10 + int((raw.end / total_duration) * 80)
                else:
                    pct = min(90, 10 + segment_count * 2)

                _emit_progress(
                    on_progress,
                    phase="transcribing",
                    percent=pct,
                    message=f"Transcribing… ({segment_count} segments)",
                    segments_completed=segment_count,
                )
        except Exception as exc:
            logger.exception("Error while processing transcription segments")
            raise TranscriptionError(
                "Failed while reading transcription segments",
                cause=str(exc),
            ) from exc

        if segments:
            total_duration = max(total_duration, segments[-1].end)

        _emit_progress(
            on_progress,
            phase="finalizing",
            percent=95,
            message="Finalizing transcript…",
            segments_completed=segment_count,
        )

        metadata = TranscriptionMetadata(
            language=detected_language,
            language_probability=(
                round(float(language_probability), 4)
                if language_probability is not None
                else None
            ),
            duration_seconds=round(total_duration, 3),
            segment_count=len(segments),
            model=settings.whisper_model,
            device=settings.whisper_device,
            backend="faster_whisper",
        )

        logger.info(
            "Transcribed %s: %d segments, duration=%.2fs, language=%s",
            audio_path.name,
            len(segments),
            total_duration,
            detected_language or "unknown",
        )

        return build_transcript_result(
            segments,
            metadata,
            max_block_duration=settings.transcript_timeline_block_seconds,
        )


def get_faster_whisper_service(settings: Settings) -> TranscriptionService:
    return FasterWhisperTranscriptionService(settings)
