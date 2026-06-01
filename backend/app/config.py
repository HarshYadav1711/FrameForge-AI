from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: str = "http://localhost:3000"

    storage_root: str = "storage"

    transcription_backend: str = "faster_whisper"
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_language: str | None = None
    whisper_beam_size: int = 1
    whisper_vad_filter: bool = True
    whisper_word_timestamps: bool = False
    whisper_initial_prompt: str = ""
    transcript_timeline_block_seconds: float = 30.0

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_enabled: bool = False

    gemini_enabled: bool = False
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    segmentation_backend: str = "auto"
    segmentation_semantic_grouping: bool = True
    scene_min_duration_seconds: float = 3.0
    scene_max_duration_seconds: float = 90.0
    scene_target_duration_seconds: float = 15.0

    video_width: int = 1920
    video_height: int = 1080
    video_fps: int = 30

    visual_default_transition: str = "fade"
    visual_transition_seconds: float = 0.5
    visual_crossfade_seconds: float = 0.35
    visual_min_scene_seconds: float = 0.5
    visual_max_asset_bytes: int = 100 * 1024 * 1024
    visual_jpeg_quality: int = 92

    subtitle_enabled: bool = True
    subtitle_theme: str = "cinematic"
    subtitle_position: str = "bottom"
    subtitle_margin_ratio: float = 0.075
    subtitle_max_width_ratio: float = 0.85
    subtitle_font_size_ratio: float = 0.042
    subtitle_line_spacing_ratio: float = 0.35
    subtitle_animation: str = "fade"
    subtitle_animation_seconds: float = 0.22
    subtitle_font_path: str = ""

    render_video_codec: str = "libx264"
    render_audio_codec: str = "aac"
    render_preset: str = "fast"
    render_crf: int = 23
    render_threads: int = 4
    render_audio_bitrate: str = "192k"
    render_video_bitrate: str | None = None
    render_pixel_format: str = "yuv420p"
    render_faststart: bool = True
    render_max_attempts: int = 2
    render_retry_delay_seconds: float = 1.0
    render_temp_subdir: str = "render_tmp"

    # fast | balanced | quality — applies speed/quality presets (see resolve_pipeline_settings)
    pipeline_profile: str = "balanced"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def storage_path(self) -> Path:
        root = Path(__file__).resolve().parent.parent
        return (root / self.storage_root).resolve()

    @property
    def jobs_path(self) -> Path:
        return self.storage_path / "jobs"

    @property
    def uploads_path(self) -> Path:
        return self.storage_path / "uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def resolve_pipeline_settings(settings: Settings) -> Settings:
    """
    Apply PIPELINE_PROFILE presets for local speed vs quality.

    Individual env vars still load first; profile adjusts known-slow defaults.
    """
    profile = settings.pipeline_profile.strip().lower()
    if profile == "fast":
        updates: dict = {
            "ollama_enabled": False,
            "gemini_enabled": False,
            "segmentation_backend": "auto",
            "whisper_beam_size": 1,
            "whisper_vad_filter": False,
            "video_width": min(settings.video_width, 1280),
            "video_height": min(settings.video_height, 720),
            "video_fps": min(settings.video_fps, 24),
            "render_preset": "veryfast",
            "render_crf": max(settings.render_crf, 28),
            "render_faststart": False,
            "subtitle_animation": "none",
            "visual_jpeg_quality": min(settings.visual_jpeg_quality, 85),
        }
        if settings.whisper_model in ("base", "small", "medium"):
            updates["whisper_model"] = "tiny"
        return settings.model_copy(update=updates)

    if profile == "quality":
        return settings.model_copy(
            update={
                "ollama_enabled": True,
                "render_preset": "medium",
                "whisper_beam_size": 5,
                "whisper_vad_filter": True,
                "render_faststart": True,
                "subtitle_animation": settings.subtitle_animation or "fade",
            }
        )

    # balanced (default): skip slow LLM, keep resolution, faster encode
    return settings.model_copy(
        update={
            "ollama_enabled": False,
            "gemini_enabled": False,
            "render_preset": (
                "fast"
                if settings.render_preset in ("medium", "slow", "slower")
                else settings.render_preset
            ),
        }
    )
