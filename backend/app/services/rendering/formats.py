"""Render output artifact persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.models.schemas import RenderOutputMetadata

logger = logging.getLogger(__name__)

ARTIFACT_VERSION = 1


def write_render_output_artifact(metadata: RenderOutputMetadata, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": ARTIFACT_VERSION, **metadata.model_dump(mode="json")}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.debug("Wrote render output metadata -> %s", path.name)


def read_render_output_artifact(path: Path) -> RenderOutputMetadata:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "version" in data:
        data = {k: v for k, v in data.items() if k != "version"}
    return RenderOutputMetadata.model_validate(data)
