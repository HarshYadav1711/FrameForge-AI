"""Scene segmentation artifact persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.models.schemas import SegmentationResult

logger = logging.getLogger(__name__)

ARTIFACT_VERSION = 1


def write_scenes_artifact(result: SegmentationResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": ARTIFACT_VERSION,
        **result.model_dump(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.debug(
        "Wrote scenes artifact %s (%d scenes)",
        path.name,
        len(result.scenes),
    )


def read_scenes_artifact(path: Path) -> SegmentationResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "version" in data and "scenes" in data:
        return SegmentationResult.model_validate(
            {k: v for k, v in data.items() if k != "version"}
        )
    # Legacy: bare scene list
    from app.models.schemas import Scene, SegmentationMetadata

    scenes = [Scene.model_validate(s) for s in data]
    return SegmentationResult(
        scenes=scenes,
        metadata=SegmentationMetadata(scene_count=len(scenes)),
    )
