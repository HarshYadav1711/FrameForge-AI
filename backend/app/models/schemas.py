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


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    GENERATED = "generated"


class TransitionType(str, Enum):
    CUT = "cut"
    FADE = "fade"
    CROSSFADE = "crossfade"


class SceneVisualMetadata(BaseModel):
    """Normalized visual asset attached to a scene."""

    media_type: MediaType = MediaType.GENERATED
    source_path: str | None = None
    normalized_path: str | None = None
    transition_in: TransitionType = TransitionType.FADE
    transition_duration_seconds: float = 0.5
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None


class SceneMetadata(BaseModel):
    """Per-scene metadata for timeline sync and future AI enhancements."""

    source: str = "heuristic"
    semantic_group: str | None = None
    transcript_segment_start: int | None = None
    transcript_segment_end: int | None = None
    word_count: int = 0
    duration_seconds: float | None = None
    visual: SceneVisualMetadata | None = None


class Scene(BaseModel):
    index: int
    title: str
    narration: str
    visual_prompt: str
    start_time: float | None = None
    end_time: float | None = None
    image_path: str | None = None
    metadata: SceneMetadata | None = None


class SegmentationMetadata(BaseModel):
    scene_count: int = 0
    total_duration_seconds: float = 0.0
    source: str = "heuristic"
    timeline_aligned: bool = False


class VisualTimelineEntry(BaseModel):
    """Single visual layer on the render timeline."""

    scene_index: int
    start: float
    end: float
    duration: float
    media_path: str
    media_type: MediaType
    transition_in: TransitionType = TransitionType.FADE
    transition_duration_seconds: float = 0.5


class VisualAssemblyMetadata(BaseModel):
    entry_count: int = 0
    total_duration_seconds: float = 0.0
    transitions_applied: int = 0
    normalized_assets: int = 0


class VisualTimeline(BaseModel):
    entries: list[VisualTimelineEntry] = Field(default_factory=list)
    metadata: VisualAssemblyMetadata = Field(default_factory=VisualAssemblyMetadata)


class SegmentationResult(BaseModel):
    scenes: list[Scene] = Field(default_factory=list)
    metadata: SegmentationMetadata = Field(default_factory=SegmentationMetadata)


class SegmentationStatusSummary(BaseModel):
    available: bool = False
    scene_count: int | None = None
    source: str | None = None
    timeline_aligned: bool | None = None
    total_duration_seconds: float | None = None


class ScenesResponse(BaseModel):
    job_id: str
    scenes: list[Scene] = Field(default_factory=list)
    metadata: SegmentationMetadata = Field(default_factory=SegmentationMetadata)


class RenderPhase(str, Enum):
    PREPARING = "preparing"
    COMPOSING = "composing"
    ENCODING = "encoding"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class RenderingProgress(BaseModel):
    """Fine-grained progress during the render step."""

    phase: RenderPhase = RenderPhase.PREPARING
    percent: int = 0
    message: str = ""
    attempt: int = 1
    frame: int | None = None
    total_frames: int | None = None


class RenderOutputMetadata(BaseModel):
    """Metadata for the exported MP4."""

    path: str
    file_size_bytes: int = 0
    duration_seconds: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    video_codec: str = ""
    audio_codec: str = ""
    video_bitrate_kbps: int | None = None
    audio_bitrate_kbps: int | None = None
    encoded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
    segmentation: SegmentationStatusSummary | None = None


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
