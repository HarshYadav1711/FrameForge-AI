"""Output metadata extraction via ffprobe with safe fallbacks."""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from app.models.schemas import RenderOutputMetadata
from app.services.rendering.config import RenderOutputConfig

logger = logging.getLogger(__name__)


def _parse_bitrate_kbps(value: str | None) -> int | None:
    if not value:
        return None
    try:
        bits = int(value)
        return max(1, bits // 1000)
    except (TypeError, ValueError):
        return None


def probe_with_ffprobe(path: Path) -> dict | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError, TimeoutError) as exc:
        logger.debug("ffprobe unavailable or failed: %s", exc)
        return None


def build_output_metadata(
    path: Path,
    config: RenderOutputConfig,
    *,
    probe: dict | None = None,
    fallback_duration: float | None = None,
) -> RenderOutputMetadata:
    """Build metadata for a rendered file."""
    probe = probe if probe is not None else probe_with_ffprobe(path)
    size = path.stat().st_size if path.exists() else 0
    duration = 0.0
    width = config.width
    height = config.height
    fps = float(config.fps)
    video_codec = config.video_codec
    audio_codec = config.audio_codec
    video_br: int | None = None
    audio_br: int | None = None

    if probe:
        fmt = probe.get("format", {})
        duration = float(fmt.get("duration", 0) or 0)
        video_br = _parse_bitrate_kbps(fmt.get("bit_rate"))
        for stream in probe.get("streams", []):
            codec_type = stream.get("codec_type")
            if codec_type == "video":
                width = int(stream.get("width", width))
                height = int(stream.get("height", height))
                video_codec = stream.get("codec_name", video_codec) or video_codec
                video_br = video_br or _parse_bitrate_kbps(stream.get("bit_rate"))
                rate = stream.get("r_frame_rate", "")
                if "/" in rate:
                    num, den = rate.split("/", 1)
                    if den != "0":
                        fps = round(int(num) / int(den), 3)
            elif codec_type == "audio":
                audio_codec = stream.get("codec_name", audio_codec) or audio_codec
                audio_br = _parse_bitrate_kbps(stream.get("bit_rate"))

    if duration <= 0 and fallback_duration and fallback_duration > 0:
        duration = float(fallback_duration)

    return RenderOutputMetadata(
        path=str(path.resolve()),
        file_size_bytes=size,
        duration_seconds=round(duration, 3),
        width=width,
        height=height,
        fps=fps,
        video_codec=video_codec,
        audio_codec=audio_codec,
        video_bitrate_kbps=video_br,
        audio_bitrate_kbps=audio_br,
        encoded_at=datetime.now(timezone.utc),
    )
