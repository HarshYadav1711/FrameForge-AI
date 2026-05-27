import json
import logging
from pathlib import Path

from app.config import Settings
from app.models.schemas import TranscriptSegment

logger = logging.getLogger(__name__)

_whisper_model = None


def _get_whisper_model(settings: Settings):
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        logger.info(
            "Loading Whisper model=%s device=%s",
            settings.whisper_model,
            settings.whisper_device,
        )
        _whisper_model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    return _whisper_model


def transcribe_audio(
    audio_path: Path,
    settings: Settings,
    *,
    transcript_out: Path | None = None,
) -> tuple[list[TranscriptSegment], float]:
    """Transcribe narration audio with Faster-Whisper."""
    model = _get_whisper_model(settings)
    segments_iter, info = model.transcribe(
        str(audio_path),
        vad_filter=True,
        word_timestamps=False,
    )

    segments: list[TranscriptSegment] = []
    for seg in segments_iter:
        segments.append(
            TranscriptSegment(
                start=round(seg.start, 3),
                end=round(seg.end, 3),
                text=seg.text.strip(),
            )
        )

    duration = float(info.duration) if info.duration else 0.0
    if segments:
        duration = max(duration, segments[-1].end)

    if transcript_out:
        transcript_out.write_text(
            json.dumps([s.model_dump() for s in segments], indent=2),
            encoding="utf-8",
        )

    logger.info(
        "Transcribed %d segments, duration=%.2fs",
        len(segments),
        duration,
    )
    return segments, duration
