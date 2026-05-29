"""Visual timeline artifact persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.models.schemas import VisualTimeline

logger = logging.getLogger(__name__)

ARTIFACT_VERSION = 1


def write_visual_timeline_artifact(timeline: VisualTimeline, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": ARTIFACT_VERSION, **timeline.model_dump()}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.debug("Wrote visual timeline artifact %s (%d entries)", path.name, len(timeline.entries))


def read_visual_timeline_artifact(path: Path) -> VisualTimeline:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "version" in data and "entries" in data:
        return VisualTimeline.model_validate({k: v for k, v in data.items() if k != "version"})
    return VisualTimeline.model_validate(data)
