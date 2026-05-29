"""Backward-compatible visual helpers; assembly lives in visual_assembly."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.models.schemas import Scene, VisualTimeline
from app.services.visual_assembly.generator import generate_scene_visual

__all__ = ["attach_visuals", "generate_scene_visual"]


def attach_visuals(
    scenes: list[Scene],
    visuals_dir: Path,
    settings: Settings,
    *,
    total_duration: float = 0.0,
) -> tuple[list[Scene], VisualTimeline]:
    """Run the visual assembly pipeline (attach, validate, normalize, timeline)."""
    from app.services.visual_assembly.pipeline import assemble_scene_visuals

    return assemble_scene_visuals(
        scenes,
        visuals_dir,
        settings,
        total_duration=total_duration,
    )
