import logging
from pathlib import Path

from app.config import Settings
from app.models.schemas import Scene, TranscriptSegment, VisualTimeline
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


def render_video(
    scenes: list[Scene],
    audio_path: Path,
    output_path: Path,
    settings: Settings,
    *,
    srt_path: Path | None = None,
    transcript_segments: list[TranscriptSegment] | None = None,
    visual_timeline: VisualTimeline | None = None,
) -> str:
    """
    Compose scene visuals + narration audio into final MP4.

    Uses the visual timeline when provided; otherwise builds one from scenes.
    Supports static images, video clips, and configurable transitions.
    """
    AudioFileClip = import_audio_file_clip()
    CompositeVideoClip = import_composite_video_clip()

    if not scenes:
        raise ValueError("No scenes to render")

    audio = AudioFileClip(str(audio_path))
    duration = audio.duration
    video_size = (settings.video_width, settings.video_height)

    timeline = visual_timeline or build_visual_timeline(scenes, duration, settings)
    if not timeline.entries:
        raise ValueError("No valid visual timeline entries")

    clips = build_clips_from_timeline(timeline.entries, video_size)
    if not clips:
        raise ValueError("No valid scene clips produced")

    video = CompositeVideoClip(clips, size=video_size)
    video = _with_duration(video, duration)

    subtitle_clips: list = []
    if subtitle_rendering_enabled(settings):
        cues = load_subtitle_cues(
            segments=transcript_segments,
            srt_path=srt_path,
        )
        if cues:
            style = resolve_style_for_video(settings)
            subtitle_clips = build_subtitle_overlay_clips(cues, style)
            video = composite_with_subtitles(video, subtitle_clips)
            logger.info(
                "Applied cinematic subtitles (%d cues, theme=%s)",
                len(cues),
                style.theme_name,
            )
        else:
            logger.warning("Subtitle rendering enabled but no cues found")

    if hasattr(video, "with_audio"):
        final = video.with_audio(audio)
    else:
        final = video.set_audio(audio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path),
        fps=settings.video_fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger=None,
    )

    audio.close()
    final.close()
    for c in clips + subtitle_clips:
        try:
            c.close()
        except Exception:
            pass

    logger.info("Rendered video -> %s", output_path)
    return str(output_path)
