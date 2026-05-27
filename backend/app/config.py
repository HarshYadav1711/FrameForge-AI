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

    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_enabled: bool = True

    gemini_enabled: bool = False
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    video_width: int = 1920
    video_height: int = 1080
    video_fps: int = 30

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
