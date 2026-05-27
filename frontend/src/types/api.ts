export interface HealthResponse {
  status: string;
  version: string;
  whisper_model: string;
  ollama_enabled: boolean;
  gemini_enabled: boolean;
}

export interface ReadinessResponse {
  status: "ready" | "not_ready";
  checks: Record<string, boolean>;
}
