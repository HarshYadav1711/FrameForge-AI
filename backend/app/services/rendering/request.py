"""Render job request model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.models.schemas import Scene, TranscriptSegment, VisualTimeline


@dataclass
class RenderRequest:
    scenes: list[Scene]
    audio_path: Path
    output_path: Path
    settings: Settings
    srt_path: Path | None = None
    transcript_segments: list[TranscriptSegment] | None = None
    visual_timeline: VisualTimeline | None = None
    job_id: str | None = None
    work_dir: Path | None = None
    state_path: Path | None = None
    metadata_path: Path | None = None

    def resolve_work_dir(self) -> Path:
        if self.work_dir:
            return self.work_dir
        return self.output_path.parent / "render_tmp"
