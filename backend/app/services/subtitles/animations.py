"""Subtitle animation helpers (fade in/out)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def apply_subtitle_animation(clip, animation: str, fade_seconds: float, cue_duration: float):
    """
    Apply lightweight fade animation synced to cue duration.

    Returns the clip unchanged when animation is disabled or too short.
    """
    if animation.lower().strip() in ("none", "off", ""):
        return clip

    if fade_seconds <= 0 or cue_duration <= 0:
        return clip

    fade = min(fade_seconds, cue_duration / 3.0)
    if fade <= 0.01:
        return clip

    try:
        from moviepy.video.fx import CrossFadeIn, CrossFadeOut

        return clip.with_effects([CrossFadeIn(fade), CrossFadeOut(fade)])
    except ImportError:
        pass

    try:
        if hasattr(clip, "crossfadein"):
            return clip.crossfadein(fade).crossfadeout(fade)
    except Exception as exc:
        logger.debug("Crossfade fallback unavailable: %s", exc)

    try:
        from moviepy.video.fx.FadeIn import FadeIn
        from moviepy.video.fx.FadeOut import FadeOut

        return clip.with_effects([FadeIn(fade), FadeOut(fade)])
    except Exception as exc:
        logger.debug("FadeIn/FadeOut unavailable: %s", exc)

    return clip
