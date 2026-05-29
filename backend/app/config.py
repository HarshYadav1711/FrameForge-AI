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
    whisper_beam_size: int = 5
    whisper_vad_filter: bool = True
    whisper_word_timestamps: bool = False
    whisper_initial_prompt: str = ""
    transcript_timeline_block_seconds: float = 30.0

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_enabled: bool = True

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
