"""Render processing lifecycle and persisted state."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.models.schemas import RenderPhase, RenderingProgress

logger = logging.getLogger(__name__)

ARTIFACT_VERSION = 1


class RenderLifecycle:
    """
    Manages render phase transitions and optional on-disk state for recovery.

    State is written to ``render_state.json`` in the job directory when a path
    is provided.
    """

    def __init__(self, state_path: Path | None = None) -> None:
        self._state_path = state_path
        self.phase = RenderPhase.PREPARING
        self.attempt = 1
        self.started_at = datetime.now(timezone.utc)
        self.last_error: str | None = None
        self.partial_path: str | None = None

    def _persist(self) -> None:
        if not self._state_path:
            return
        payload = {
            "version": ARTIFACT_VERSION,
            "phase": self.phase.value,
            "attempt": self.attempt,
            "started_at": self.started_at.isoformat(),
            "last_error": self.last_error,
            "partial_path": self.partial_path,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def transition(self, phase: RenderPhase, *, error: str | None = None) -> None:
        self.phase = phase
        if error:
            self.last_error = error
        self._persist()
        logger.debug("Render lifecycle -> %s", phase.value)

    def set_partial(self, path: Path) -> None:
        self.partial_path = str(path.resolve())
        self._persist()

    def mark_attempt(self, attempt: int) -> None:
        self.attempt = attempt
        self._persist()

    def clear_state(self) -> None:
        if self._state_path and self._state_path.exists():
            self._state_path.unlink(missing_ok=True)

    @classmethod
    def load(cls, state_path: Path) -> RenderLifecycle | None:
        if not state_path.exists():
            return None
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            lifecycle = cls(state_path=state_path)
            lifecycle.phase = RenderPhase(data.get("phase", "preparing"))
            lifecycle.attempt = int(data.get("attempt", 1))
            lifecycle.last_error = data.get("last_error")
            lifecycle.partial_path = data.get("partial_path")
            return lifecycle
        except Exception as exc:
            logger.warning("Could not load render state: %s", exc)
            return None


def pipeline_percent_from_render(progress: RenderingProgress) -> int:
    """Map render-phase percent (0–100) to pipeline step percent (85–99)."""
    return min(99, 85 + int(progress.percent * 0.14))
