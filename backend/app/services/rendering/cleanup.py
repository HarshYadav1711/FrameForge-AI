"""Resource cleanup for render jobs."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class ClipResourceManager:
    """Track and close MoviePy clips reliably."""

    def __init__(self) -> None:
        self._clips: list = []

    def track(self, clip):
        if clip is not None:
            self._clips.append(clip)
        return clip

    def close_all(self) -> None:
        for clip in reversed(self._clips):
            try:
                clip.close()
            except Exception as exc:
                logger.debug("Clip close ignored: %s", exc)
        self._clips.clear()


def partial_output_path(output_path: Path) -> Path:
    return output_path.with_suffix(output_path.suffix + ".partial")


def remove_partial_output(output_path: Path) -> None:
    partial = partial_output_path(output_path)
    if partial.exists():
        partial.unlink(missing_ok=True)
        logger.debug("Removed partial output %s", partial.name)


def promote_partial_output(output_path: Path) -> None:
    """Atomically replace final output with completed partial file."""
    partial = partial_output_path(output_path)
    if not partial.exists():
        raise FileNotFoundError(f"Partial render missing: {partial}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    partial.replace(output_path)


def cleanup_render_temp(temp_dir: Path) -> None:
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.debug("Cleaned render temp dir %s", temp_dir)


def ensure_clean_output_slot(output_path: Path) -> None:
    """Remove stale outputs before a new render attempt."""
    remove_partial_output(output_path)
    if output_path.exists():
        output_path.unlink(missing_ok=True)
