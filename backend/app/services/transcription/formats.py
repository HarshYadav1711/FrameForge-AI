"""Persist and load structured transcription artifacts."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.models.schemas import TranscriptResult

logger = logging.getLogger(__name__)

ARTIFACT_VERSION = 1


def write_transcript_artifact(result: TranscriptResult, path: Path) -> None:
    """Write subtitle-ready, timeline-aware transcript JSON to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": ARTIFACT_VERSION,
        **result.model_dump(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.debug(
        "Wrote transcript artifact %s (%d segments, %d timeline blocks)",
        path.name,
        len(result.segments),
        len(result.timeline_blocks),
    )


def read_transcript_artifact(path: Path) -> TranscriptResult:
    """Load a transcript artifact written by write_transcript_artifact."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if "version" in data and "segments" in data:
        return TranscriptResult.model_validate(
            {k: v for k, v in data.items() if k != "version"}
        )
    # Legacy flat segment list
    from app.models.schemas import TranscriptSegment, TranscriptionMetadata

    segments = [TranscriptSegment.model_validate(s) for s in data]
    from app.services.transcription.base import build_transcript_result

    return build_transcript_result(
        segments,
        TranscriptionMetadata(segment_count=len(segments)),
    )
