"""Build timeline-synced subtitle overlay clips for video compositing."""

from __future__ import annotations

import logging
from typing import Any

from app.config import Settings
from app.models.schemas import SubtitleCue
from app.services.subtitles.animations import apply_subtitle_animation
from app.services.subtitles.config import (
    ResolvedSubtitleStyle,
    resolve_subtitle_style,
    style_config_from_settings,
)
from app.services.subtitles.moviepy_compat import (
    import_composite_video_clip,
    rgba_array_to_clip,
    with_position,
    with_start,
)
from app.services.subtitles.render_helpers import (
    compute_overlay_position,
    render_subtitle_rgba,
)
from app.services.subtitles.themes import get_theme
from app.services.subtitles.utils import cue_duration, normalize_cues

logger = logging.getLogger(__name__)


def resolve_style_for_video(settings: Settings) -> ResolvedSubtitleStyle:
    config = style_config_from_settings(settings)
    theme = get_theme(config.theme)
    return resolve_subtitle_style(
        config,
        theme,
        video_width=settings.video_width,
        video_height=settings.video_height,
    )


def build_subtitle_overlay_clips(
    cues: list[SubtitleCue],
    style: ResolvedSubtitleStyle,
) -> list[Any]:
    """
    Create MoviePy clips for each subtitle cue, positioned and timed on the timeline.
    """
    normalized = normalize_cues(cues)
    clips: list[Any] = []

    for cue in normalized:
        duration = cue_duration(cue)
        if duration <= 0 or not cue.text.strip():
            continue

        rgba = render_subtitle_rgba(cue.text, style)
        h, w = rgba.shape[:2]
        position = compute_overlay_position(style, w, h)

        clip = rgba_array_to_clip(rgba, duration)
        clip = with_start(clip, cue.start)
        clip = with_position(clip, position)

        clip = apply_subtitle_animation(
            clip,
            style.animation,
            style.animation_seconds,
            duration,
        )
        clips.append(clip)

    logger.info(
        "Built %d subtitle overlays (theme=%s, %dx%d)",
        len(clips),
        style.theme_name,
        style.video_width,
        style.video_height,
    )
    return clips


def composite_with_subtitles(
    base_clip: Any,
    subtitle_clips: list[Any],
) -> Any:
    """Layer subtitle overlays on top of a base video clip."""
    if not subtitle_clips:
        return base_clip

    CompositeVideoClip = import_composite_video_clip()
    size = (base_clip.w, base_clip.h)
    return CompositeVideoClip(
        [base_clip, *subtitle_clips],
        size=size,
    )
