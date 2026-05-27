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


class TranscriptWord(BaseModel):
    start: float
    end: float
    word: str


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    confidence: float | None = None
    words: list[TranscriptWord] | None = None


class SubtitleCue(BaseModel):
    index: int
    start: float
    end: float
    text: str


class TranscriptTimelineBlock(BaseModel):
    """Merged segment block for scene segmentation and timeline sync."""

    index: int
    start: float
    end: float
    text: str


class TranscriptionMetadata(BaseModel):
    language: str | None = None
    language_probability: float | None = None
    duration_seconds: float = 0.0
    segment_count: int = 0
    model: str = ""
    device: str = ""
    backend: str = "faster_whisper"


class TranscriptionProgress(BaseModel):
    phase: str = "transcribing"
    percent: int = 0
    message: str = ""
    segments_completed: int = 0


class TranscriptResult(BaseModel):
    """Structured transcription output for subtitles, scenes, and timeline sync."""

    segments: list[TranscriptSegment] = Field(default_factory=list)
    timeline_blocks: list[TranscriptTimelineBlock] = Field(default_factory=list)
    subtitle_cues: list[SubtitleCue] = Field(default_factory=list)
    metadata: TranscriptionMetadata = Field(default_factory=TranscriptionMetadata)


class TranscriptionStatusSummary(BaseModel):
    available: bool = False
    segment_count: int | None = None
    duration_seconds: float | None = None
    language: str | None = None
    language_probability: float | None = None
    model: str | None = None
    backend: str | None = None


class TranscriptResponse(BaseModel):
    job_id: str
    segments: list[TranscriptSegment] = Field(default_factory=list)
    timeline_blocks: list[TranscriptTimelineBlock] = Field(default_factory=list)
    subtitle_cues: list[SubtitleCue] = Field(default_factory=list)
    metadata: TranscriptionMetadata = Field(default_factory=TranscriptionMetadata)


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
    transcription: TranscriptionStatusSummary | None = None


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
