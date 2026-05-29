"""MoviePy / FFmpeg export helpers."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from app.models.schemas import RenderPhase
from app.services.rendering.cleanup import partial_output_path
from app.services.rendering.config import RenderOutputConfig
from app.services.rendering.progress import RenderProgressReporter, make_proglog_logger

logger = logging.getLogger(__name__)


def export_video_clip(
    clip,
    output_path: Path,
    config: RenderOutputConfig,
    temp_dir: Path,
    reporter: RenderProgressReporter,
) -> Path:
    """Encode clip to a partial MP4; caller promotes to final path."""
    partial = partial_output_path(output_path)
    partial.parent.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    write_kwargs = config.write_kwargs()
    proglog = make_proglog_logger(reporter)
    if proglog is not None:
        write_kwargs["logger"] = proglog

    reporter.report(RenderPhase.ENCODING, 40, "Encoding video…")

    temp_audio = temp_dir / "temp-audio.m4a"
    clip.write_videofile(
        str(partial),
        temp_audiofile=str(temp_audio),
        remove_temp=True,
        **write_kwargs,
    )

    if config.faststart:
        _apply_faststart_remux(partial)

    reporter.report(RenderPhase.ENCODING, 94, "Encode complete")
    return partial


def _apply_faststart_remux(path: Path) -> None:
    """Remux in place so the moov atom is at the front (web streaming)."""
    temp_out = path.with_suffix(path.suffix + ".faststart")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(path),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(temp_out),
            ],
            capture_output=True,
            check=True,
            timeout=600,
        )
        temp_out.replace(path)
        logger.debug("Applied faststart remux to %s", path.name)
    except (FileNotFoundError, subprocess.CalledProcessError, TimeoutError) as exc:
        logger.debug("faststart remux skipped: %s", exc)
        if temp_out.exists():
            temp_out.unlink(missing_ok=True)
