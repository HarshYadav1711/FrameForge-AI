"""Compose visuals, subtitles, and narration into a single video clip."""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import Settings
from app.models.schemas import Scene, TranscriptSegment, VisualTimeline
from app.services.rendering.cleanup import ClipResourceManager
from app.services.rendering.config import RenderOutputConfig
from app.services.subtitles import (
    build_subtitle_overlay_clips,
    composite_with_subtitles,
    load_subtitle_cues,
    resolve_style_for_video,
    subtitle_rendering_enabled,
)
from app.services.subtitles.moviepy_compat import import_audio_file_clip, import_composite_video_clip
from app.services.visual_assembly.clips import build_clips_from_timeline
from app.services.visual_assembly.timeline import build_visual_timeline

logger = logging.getLogger(__name__)


def _with_duration(clip, duration: float):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


class ComposedVideo:
    """Final clip plus resources to close after export."""

    def __init__(self, clip, resources: ClipResourceManager, *, duration: float) -> None:
        self.clip = clip
        self.resources = resources
        self.duration = duration


def compose_video(
    scenes: list[Scene],
    audio_path: Path,
    settings: Settings,
    config: RenderOutputConfig,
    resources: ClipResourceManager,
    *,
    srt_path: Path | None = None,
    transcript_segments: list[TranscriptSegment] | None = None,
    visual_timeline: VisualTimeline | None = None,
) -> ComposedVideo:
    """
    Build a composite clip: scene visuals + burned-in subtitles + narration audio.
    """
    AudioFileClip = import_audio_file_clip()
    CompositeVideoClip = import_composite_video_clip()

    if not scenes:
        raise ValueError("No scenes to render")

    audio = resources.track(AudioFileClip(str(audio_path)))
    duration = float(audio.duration or 0.0)
    if duration <= 0:
        raise ValueError("Narration audio has no duration")

    timeline = visual_timeline or build_visual_timeline(scenes, duration, settings)
    if not timeline.entries:
        raise ValueError("No valid visual timeline entries")

    scene_clips = build_clips_from_timeline(timeline.entries, config.size)
    if not scene_clips:
        raise ValueError("No valid scene clips produced")

    for clip in scene_clips:
        resources.track(clip)

    video = resources.track(CompositeVideoClip(scene_clips, size=config.size))
    video = _with_duration(video, duration)

    if subtitle_rendering_enabled(settings):
        cues = load_subtitle_cues(
            segments=transcript_segments,
            srt_path=srt_path,
        )
        if cues:
            style = resolve_style_for_video(settings)
            subtitle_clips = build_subtitle_overlay_clips(cues, style)
            for sub in subtitle_clips:
                resources.track(sub)
            video = composite_with_subtitles(video, subtitle_clips)
            logger.info(
                "Composed subtitles (%d cues, theme=%s)",
                len(cues),
                style.theme_name,
            )
        else:
            logger.warning("Subtitle rendering enabled but no cues found")

    if hasattr(video, "with_audio"):
        final = video.with_audio(audio)
    else:
        final = video.set_audio(audio)

    resources.track(final)
    return ComposedVideo(final, resources, duration=duration)
