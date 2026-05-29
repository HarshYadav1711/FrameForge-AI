export type JobStatus =
  | "pending"
  | "transcribing"
  | "segmenting"
  | "attaching_visuals"
  | "generating_subtitles"
  | "rendering"
  | "completed"
  | "failed";

export type PipelineStep =
  | "transcribe"
  | "segment"
  | "visuals"
  | "subtitles"
  | "render";

export interface JobProgress {
  step: PipelineStep | null;
  percent: number;
  message: string;
}

export interface TranscriptionStatusSummary {
  available: boolean;
  segment_count: number | null;
  duration_seconds: number | null;
  language: string | null;
  language_probability: number | null;
  model: string | null;
  backend: string | null;
}

export interface TranscriptWord {
  start: number;
  end: number;
  word: string;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  confidence?: number | null;
  words?: TranscriptWord[] | null;
}

export interface SubtitleCue {
  index: number;
  start: number;
  end: number;
  text: string;
}

export interface TranscriptTimelineBlock {
  index: number;
  start: number;
  end: number;
  text: string;
}

export interface TranscriptionMetadata {
  language: string | null;
  language_probability: number | null;
  duration_seconds: number;
  segment_count: number;
  model: string;
  device: string;
  backend: string;
}

export interface TranscriptResponse {
  job_id: string;
  segments: TranscriptSegment[];
  timeline_blocks: TranscriptTimelineBlock[];
  subtitle_cues: SubtitleCue[];
  metadata: TranscriptionMetadata;
}

export type MediaType = "image" | "video" | "generated";

export type TransitionType = "cut" | "fade" | "crossfade";

export interface SceneVisualMetadata {
  media_type: MediaType;
  source_path: string | null;
  normalized_path: string | null;
  transition_in: TransitionType;
  transition_duration_seconds: number;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
}

export interface SceneMetadata {
  source: string;
  semantic_group: string | null;
  transcript_segment_start: number | null;
  transcript_segment_end: number | null;
  word_count: number;
  duration_seconds: number | null;
  visual?: SceneVisualMetadata | null;
}

export interface Scene {
  index: number;
  title: string;
  narration: string;
  visual_prompt: string;
  start_time: number | null;
  end_time: number | null;
  image_path: string | null;
  metadata: SceneMetadata | null;
}

export interface SegmentationMetadata {
  scene_count: number;
  total_duration_seconds: number;
  source: string;
  timeline_aligned: boolean;
}

export interface SegmentationStatusSummary {
  available: boolean;
  scene_count: number | null;
  source: string | null;
  timeline_aligned: boolean | null;
  total_duration_seconds: number | null;
}

export interface ScenesResponse {
  job_id: string;
  scenes: Scene[];
  metadata: SegmentationMetadata;
}

export interface JobStatusResponse {
  id: string;
  status: JobStatus;
  progress: JobProgress;
  created_at: string;
  updated_at: string;
  error: string | null;
  scenes_count: number | null;
  video_url: string | null;
  duration_seconds: number | null;
  transcription: TranscriptionStatusSummary | null;
  segmentation: SegmentationStatusSummary | null;
}

export interface CreateJobResponse {
  id: string;
  status: JobStatus;
  message: string;
}
