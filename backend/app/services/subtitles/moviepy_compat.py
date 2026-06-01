"""MoviePy import compatibility (v1 editor API and v2 package API)."""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def import_image_clip():
    try:
        from moviepy import ImageClip

        return ImageClip
    except ImportError:
        from moviepy.editor import ImageClip

        return ImageClip


def import_composite_video_clip():
    try:
        from moviepy import CompositeVideoClip

        return CompositeVideoClip
    except ImportError:
        from moviepy.editor import CompositeVideoClip

        return CompositeVideoClip


def import_audio_file_clip():
    try:
        from moviepy import AudioFileClip

        return AudioFileClip
    except ImportError:
        from moviepy.editor import AudioFileClip

        return AudioFileClip


def import_video_file_clip():
    try:
        from moviepy import VideoFileClip

        return VideoFileClip
    except ImportError:
        from moviepy.editor import VideoFileClip

        return VideoFileClip


def rgba_array_to_clip(rgba: np.ndarray, duration: float):
    """Create a video clip from an RGBA numpy array."""
    ImageClip = import_image_clip()

    try:
        clip = ImageClip(rgba, is_mask=False, transparent=True)
        return _with_duration(clip, duration)
    except TypeError:
        pass

    try:
        clip = ImageClip(rgba, transparent=True)
        return _with_duration(clip, duration)
    except TypeError:
        pass

    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3].astype(np.float64) / 255.0
    clip = ImageClip(rgb)
    mask = ImageClip(alpha, ismask=True)
    clip = _set_mask(clip, mask)
    return _with_duration(clip, duration)


def _with_duration(clip, duration: float):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


def _set_mask(clip, mask):
    if hasattr(clip, "with_mask"):
        return clip.with_mask(mask)
    return clip.set_mask(mask)


def with_start(clip, start: float):
    if hasattr(clip, "with_start"):
        return clip.with_start(start)
    return clip.set_start(start)


def with_position(clip, position):
    if hasattr(clip, "with_position"):
        return clip.with_position(position)
    return clip.set_position(position)


def without_audio(clip):
    """Remove any audio track from a clip before attaching narration."""
    if clip is None:
        return clip
    if hasattr(clip, "without_audio"):
        try:
            return clip.without_audio()
        except Exception:
            pass
    if hasattr(clip, "audio") and clip.audio is not None:
        try:
            clip.audio = None
        except Exception:
            pass
    return clip


def with_effects(clip, effects: list):
    if hasattr(clip, "with_effects"):
        return clip.with_effects(effects)
    result = clip
    for effect in effects:
        if hasattr(result, "fx"):
            result = result.fx(effect)
    return result
