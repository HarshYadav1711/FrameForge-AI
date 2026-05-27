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
}

export interface CreateJobResponse {
  id: string;
  status: JobStatus;
  message: string;
}
