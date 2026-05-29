"""Automated visual assembly: attach media, normalize, timeline, transitions."""

from app.services.visual_assembly.assets import (
    find_scene_media,
    media_type_for_path,
    validate_media_asset,
)
from app.services.visual_assembly.formats import (
    read_visual_timeline_artifact,
    write_visual_timeline_artifact,
)
from app.services.visual_assembly.normalize import normalize_image_for_render
from app.services.visual_assembly.pipeline import assemble_scene_visuals
from app.services.visual_assembly.timeline import build_visual_timeline

__all__ = [
    "assemble_scene_visuals",
    "build_visual_timeline",
    "find_scene_media",
    "media_type_for_path",
    "normalize_image_for_render",
    "read_visual_timeline_artifact",
    "validate_media_asset",
    "write_visual_timeline_artifact",
]
