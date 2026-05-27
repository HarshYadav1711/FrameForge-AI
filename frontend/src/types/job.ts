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
}

export interface CreateJobResponse {
  id: string;
  status: JobStatus;
  message: string;
}
