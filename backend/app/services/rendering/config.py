"""Render output configuration derived from application settings."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class RenderOutputConfig:
    width: int
    height: int
    fps: int
    video_codec: str
    audio_codec: str
    preset: str
    crf: int
    threads: int
    audio_bitrate: str
    video_bitrate: str | None
    pixel_format: str
    faststart: bool
    max_attempts: int
    retry_delay_seconds: float
    temp_subdir: str

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    def ffmpeg_params(self) -> list[str]:
        params = ["-pix_fmt", self.pixel_format, "-crf", str(self.crf)]
        if self.faststart:
            params.extend(["-movflags", "+faststart"])
        return params

    def write_kwargs(self) -> dict:
        """Keyword arguments for MoviePy write_videofile."""
        kwargs: dict = {
            "fps": self.fps,
            "codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "preset": self.preset,
            "threads": self.threads,
            "ffmpeg_params": self.ffmpeg_params(),
            "audio_bitrate": self.audio_bitrate,
            "logger": None,
        }
        if self.video_bitrate:
            kwargs["bitrate"] = self.video_bitrate
        return kwargs


def render_config_from_settings(settings: Settings) -> RenderOutputConfig:
    return RenderOutputConfig(
        width=settings.video_width,
        height=settings.video_height,
        fps=settings.video_fps,
        video_codec=settings.render_video_codec,
        audio_codec=settings.render_audio_codec,
        preset=settings.render_preset,
        crf=settings.render_crf,
        threads=settings.render_threads,
        audio_bitrate=settings.render_audio_bitrate,
        video_bitrate=settings.render_video_bitrate,
        pixel_format=settings.render_pixel_format,
        faststart=settings.render_faststart,
        max_attempts=max(1, settings.render_max_attempts),
        retry_delay_seconds=settings.render_retry_delay_seconds,
        temp_subdir=settings.render_temp_subdir,
    )
