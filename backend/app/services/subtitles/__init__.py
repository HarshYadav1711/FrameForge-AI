"""Cinematic subtitle system — SRT, styling, and video overlays."""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import Settings
from app.models.schemas import SubtitleCue, TranscriptSegment
from app.services.subtitles.config import (
    ResolvedSubtitleStyle,
    SubtitleStyleConfig,
    SubtitleThemeDefinition,
    resolve_subtitle_style,
    style_config_from_settings,
)
from app.services.subtitles.overlays import (
    build_subtitle_overlay_clips,
    composite_with_subtitles,
    resolve_style_for_video,
)
from app.services.subtitles.srt import generate_srt, generate_srt_from_cues
from app.services.subtitles.themes import THEME_PRESETS, get_theme
from app.services.subtitles.utils import (
    cues_from_segments,
    normalize_cues,
    parse_srt_content,
    parse_srt_file,
)

logger = logging.getLogger(__name__)

__all__ = [
    "THEME_PRESETS",
    "ResolvedSubtitleStyle",
    "SubtitleStyleConfig",
    "SubtitleThemeDefinition",
    "build_subtitle_overlay_clips",
    "composite_with_subtitles",
    "cues_from_segments",
    "generate_srt",
    "generate_srt_from_cues",
    "get_theme",
    "load_subtitle_cues",
    "normalize_cues",
    "parse_srt_content",
    "parse_srt_file",
    "resolve_style_for_video",
    "resolve_subtitle_style",
    "style_config_from_settings",
]


def load_subtitle_cues(
    *,
    segments: list[TranscriptSegment] | None = None,
    srt_path: Path | None = None,
) -> list[SubtitleCue]:
    """Load cues from transcript segments or an SRT file."""
    if segments:
        return normalize_cues(cues_from_segments(segments))
    if srt_path and srt_path.exists():
        return parse_srt_file(srt_path)
    return []


def subtitle_rendering_enabled(settings: Settings) -> bool:
    return style_config_from_settings(settings).enabled
