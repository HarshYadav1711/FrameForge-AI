import logging
from pathlib import Path

from app.config import Settings
from app.models.schemas import Scene

logger = logging.getLogger(__name__)


def render_video(
    scenes: list[Scene],
    audio_path: Path,
    output_path: Path,
    settings: Settings,
    *,
    srt_path: Path | None = None,
) -> str:
    """
    Compose scene images + narration audio into final MP4.
    Uses MoviePy 2.x API.
    """
    from moviepy import (
        AudioFileClip,
        CompositeVideoClip,
        ImageClip,
        TextClip,
        concatenate_videoclips,
    )

    if not scenes:
        raise ValueError("No scenes to render")

    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    clips = []
    for scene in scenes:
        if not scene.image_path or not Path(scene.image_path).exists():
            continue
        start = scene.start_time or 0.0
        end = scene.end_time or duration
        clip_duration = max(end - start, 0.5)

        img_clip = ImageClip(scene.image_path).with_duration(clip_duration)
        img_clip = img_clip.resized(
            new_size=(settings.video_width, settings.video_height)
        )

        overlay_clips = [img_clip]
        if scene.narration:
            try:
                txt = (
                    TextClip(
                        text=scene.narration[:200],
                        font_size=36,
                        color="white",
                        stroke_color="black",
                        stroke_width=1,
                        method="caption",
                        size=(settings.video_width - 160, None),
                    )
                    .with_duration(clip_duration)
                    .with_position(("center", "bottom"))
                )
                overlay_clips.append(txt)
            except Exception as exc:
                logger.warning("Subtitle overlay skipped for scene %d: %s", scene.index, exc)

        scene_clip = CompositeVideoClip(overlay_clips, size=(settings.video_width, settings.video_height))
        scene_clip = scene_clip.with_start(start)
        clips.append(scene_clip)

    if not clips:
        raise ValueError("No valid scene clips produced")

    video = CompositeVideoClip(clips, size=(settings.video_width, settings.video_height))
    video = video.with_duration(duration)
    final = video.with_audio(audio)

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
    for c in clips:
        c.close()

    logger.info("Rendered video -> %s", output_path)
    return str(output_path)
