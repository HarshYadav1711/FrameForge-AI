import { env } from "@/config/env";
import { apiRequest } from "@/lib/http/client";
import type {
  CreateJobResponse,
  JobStatusResponse,
  ScenesResponse,
  TranscriptResponse,
} from "@/types/job";

export function createJob(
  script: string,
  uploadId: string,
): Promise<CreateJobResponse> {
  const form = new FormData();
  form.append("script", script);
  form.append("upload_id", uploadId);

  return apiRequest<CreateJobResponse>("/api/v1/jobs", {
    method: "POST",
    body: form,
  });
}

export function getJob(jobId: string): Promise<JobStatusResponse> {
  return apiRequest<JobStatusResponse>(`/api/v1/jobs/${jobId}`, {
    cache: "no-store",
  });
}

export function getJobTranscript(jobId: string): Promise<TranscriptResponse> {
  return apiRequest<TranscriptResponse>(`/api/v1/jobs/${jobId}/transcript`, {
    cache: "no-store",
  });
}

export function getJobScenes(jobId: string): Promise<ScenesResponse> {
  return apiRequest<ScenesResponse>(`/api/v1/jobs/${jobId}/scenes`, {
    cache: "no-store",
  });
}

export function videoDownloadUrl(jobId: string): string {
  return `${env.apiUrl}/api/v1/jobs/${jobId}/video`;
}
