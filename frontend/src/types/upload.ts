export interface AudioUploadResponse {
  id: string;
  original_filename: string;
  sanitized_filename: string;
  extension: string;
  size_bytes: number;
  content_type: string | null;
  message: string;
}

export type UploadPhase = "idle" | "validating" | "uploading" | "complete" | "error";

export interface AudioUploadState {
  phase: UploadPhase;
  progress: number;
  uploadId: string | null;
  error: string | null;
}
