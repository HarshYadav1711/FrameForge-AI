from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    TRANSCRIBING = "transcribing"
    SEGMENTING = "segmenting"
    ATTACHING_VISUALS = "attaching_visuals"
    GENERATING_SUBTITLES = "generating_subtitles"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStep(str, Enum):
    TRANSCRIBE = "transcribe"
    SEGMENT = "segment"
    VISUALS = "visuals"
    SUBTITLES = "subtitles"
    RENDER = "render"


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class Scene(BaseModel):
    index: int
    title: str
    narration: str
    visual_prompt: str
    start_time: float | None = None
    end_time: float | None = None
    image_path: str | None = None


class JobProgress(BaseModel):
    step: PipelineStep | None = None
    percent: int = 0
    message: str = ""


class JobStatusResponse(BaseModel):
    id: str
    status: JobStatus
    progress: JobProgress
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    scenes_count: int | None = None
    video_url: str | None = None
    duration_seconds: float | None = None


class CreateJobResponse(BaseModel):
    id: str
    status: JobStatus
    message: str = "Job created and processing started"


class AudioUploadResponse(BaseModel):
    id: str
    original_filename: str
    sanitized_filename: str
    extension: str
    size_bytes: int
    content_type: str | None = None
    message: str = "Audio uploaded successfully"


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    whisper_model: str
    ollama_enabled: bool
    gemini_enabled: bool


class LivenessResponse(BaseModel):
    status: str = "alive"


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, bool]


class JobRecord(BaseModel):
    """Persisted job state (file-backed, no database)."""

    id: str
    status: JobStatus = JobStatus.PENDING
    progress: JobProgress = Field(default_factory=JobProgress)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None
    script: str = ""
    audio_filename: str = ""
    scenes: list[Scene] = Field(default_factory=list)
    transcript: list[TranscriptSegment] = Field(default_factory=list)
    duration_seconds: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
