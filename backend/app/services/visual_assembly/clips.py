"""Build MoviePy clips from visual timeline entries."""

from __future__ import annotations

from pathlib import Path

from app.models.schemas import MediaType, VisualTimelineEntry
from app.services.subtitles.moviepy_compat import (
    import_composite_video_clip,
    import_image_clip,
    import_video_file_clip,
    without_audio,
    with_start,
)
from app.services.visual_assembly.transitions import (
    apply_transition_in,
    transition_overlap_seconds,
)


def _with_duration(clip, duration: float):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


def _resized(clip, size: tuple[int, int]):
    if hasattr(clip, "resized"):
        return clip.resized(new_size=size)
    return clip.resize(size)


def _subclip(clip, start: float, end: float):
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start, end)
    return clip.subclip(start, end)


def build_scene_clip(
    entry: VisualTimelineEntry,
    video_size: tuple[int, int],
    *,
    overlap_start: float = 0.0,
) -> object:
    """Create a sized scene clip with optional incoming transition."""
    ImageClip = import_image_clip()
    VideoFileClip = import_video_file_clip()
    CompositeVideoClip = import_composite_video_clip()

    media_path = Path(entry.media_path)
    if entry.media_type == MediaType.VIDEO:
        if not media_path.exists():
            raise FileNotFoundError(f"Video not found: {media_path}")
        clip = VideoFileClip(str(media_path))
        clip = without_audio(clip)
        if clip.duration and clip.duration > entry.duration:
            clip = _subclip(clip, 0, entry.duration)
        clip = _with_duration(clip, entry.duration)
    else:
        if not media_path.exists():
            raise FileNotFoundError(f"Visual not found: {media_path}")
        clip = _with_duration(ImageClip(str(media_path)), entry.duration)

    clip = _resized(clip, video_size)
    base = CompositeVideoClip([clip], size=video_size)

    effective_start = entry.start - overlap_start
    base = with_start(base, max(effective_start, 0.0))

    if entry.transition_in.value != "cut":
        base = apply_transition_in(
            base,
            entry.transition_in,
            entry.transition_duration_seconds,
        )

    return base


def build_clips_from_timeline(
    entries: list[VisualTimelineEntry],
    video_size: tuple[int, int],
) -> list:
    """Build all scene clips, accounting for crossfade overlap."""
    clips: list = []
    prev_overlap = 0.0

    for entry in entries:
        overlap = transition_overlap_seconds(
            entry.transition_in,
            entry.transition_duration_seconds,
        )
        clip = build_scene_clip(
            entry,
            video_size,
            overlap_start=prev_overlap,
        )
        clips.append(clip)
        prev_overlap = overlap

    return clips
