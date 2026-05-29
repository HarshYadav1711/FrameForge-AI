"""Rendering progress reporting for pipeline and encode callbacks."""

from __future__ import annotations

import logging
from typing import Callable, Protocol

from app.models.schemas import RenderPhase, RenderingProgress

logger = logging.getLogger(__name__)

# Encode step spans this slice of overall render percent (0–100).
ENCODE_PERCENT_START = 38
ENCODE_PERCENT_END = 94


class ProgressCallback(Protocol):
    def __call__(self, progress: RenderingProgress) -> None: ...


class RenderProgressReporter:
    """Maps lifecycle phases to pipeline percent and optional encode frames."""

    def __init__(
        self,
        on_progress: ProgressCallback | None = None,
        *,
        attempt: int = 1,
    ) -> None:
        self._on_progress = on_progress
        self._attempt = attempt

    def report(
        self,
        phase: RenderPhase,
        percent: int,
        message: str,
        *,
        frame: int | None = None,
        total_frames: int | None = None,
    ) -> None:
        progress = RenderingProgress(
            phase=phase,
            percent=max(0, min(100, percent)),
            message=message,
            attempt=self._attempt,
            frame=frame,
            total_frames=total_frames,
        )
        if self._on_progress:
            self._on_progress(progress)
        logger.debug(
            "Render progress [%s] %d%% — %s (attempt %d)",
            phase.value,
            progress.percent,
            message,
            self._attempt,
        )

    def report_encode_frame(self, frame: int, total_frames: int) -> None:
        if total_frames <= 0:
            return
        ratio = frame / total_frames
        percent = ENCODE_PERCENT_START + int(
            ratio * (ENCODE_PERCENT_END - ENCODE_PERCENT_START)
        )
        self.report(
            RenderPhase.ENCODING,
            percent,
            f"Encoding frame {frame}/{total_frames}",
            frame=frame,
            total_frames=total_frames,
        )


def make_proglog_logger(reporter: RenderProgressReporter):
    """Build a MoviePy/proglog logger that forwards encode progress."""
    try:
        from proglog import ProgressBarLogger
    except ImportError:
        return None

    class _RenderLogger(ProgressBarLogger):  # type: ignore[misc]
        def bars_callback(self, bar, attr, value, old_value=None):
            super().bars_callback(bar, attr, value, old_value=old_value)
            if bar != "t" or attr != "index":
                return
            bars = self.bars.get("t")
            if not bars:
                return
            total = bars.get("total") or 0
            if total:
                reporter.report_encode_frame(int(value), int(total))

    return _RenderLogger()
