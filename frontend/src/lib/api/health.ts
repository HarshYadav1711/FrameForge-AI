import { apiRequest } from "@/lib/http/client";
import type { HealthResponse, ReadinessResponse } from "@/types/api";

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/api/v1/health");
}

export function getReadiness(): Promise<ReadinessResponse> {
  return apiRequest<ReadinessResponse>("/api/v1/health/ready");
}
