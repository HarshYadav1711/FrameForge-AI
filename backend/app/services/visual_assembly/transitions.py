"""Transition effects for scene clips."""

from __future__ import annotations

import logging

from app.models.schemas import TransitionType

logger = logging.getLogger(__name__)


def _fade_in(clip, duration: float):
    if duration <= 0:
        return clip
    if hasattr(clip, "fadein"):
        return clip.fadein(duration)
    try:
        from moviepy.video.fx.FadeIn import FadeIn

        return clip.with_effects([FadeIn(duration)])
    except Exception:
        try:
            from moviepy.editor import vfx

            return clip.fx(vfx.fadein, duration)
        except Exception:
            logger.warning("Fade-in unavailable; using cut transition")
            return clip


def _crossfade(clip, duration: float):
    if duration <= 0:
        return clip
    if hasattr(clip, "crossfadein"):
        return clip.crossfadein(duration)
    return _fade_in(clip, duration)


def apply_transition_in(clip, transition: TransitionType, duration: float):
    """Apply an incoming transition to a clip."""
    if transition == TransitionType.CUT:
        return clip
    if transition == TransitionType.CROSSFADE:
        return _crossfade(clip, duration)
    return _fade_in(clip, duration)


def transition_overlap_seconds(transition: TransitionType, duration: float) -> float:
    """How much timeline overlap this transition needs with the previous clip."""
    if transition == TransitionType.CROSSFADE:
        return max(duration, 0.0)
    return 0.0
