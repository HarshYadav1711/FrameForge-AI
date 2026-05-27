import { env } from "@/config/env";
import { apiRequest } from "@/lib/http/client";
import type { CreateJobResponse, JobStatusResponse } from "@/types/job";

export function createJob(script: string, audio: File): Promise<CreateJobResponse> {
  const form = new FormData();
  form.append("script", script);
  form.append("audio", audio);

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

export function videoDownloadUrl(jobId: string): string {
  return `${env.apiUrl}/api/v1/jobs/${jobId}/video`;
}
