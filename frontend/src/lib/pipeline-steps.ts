import type { LucideIcon } from "lucide-react";
import { Clapperboard, Film, Image, Mic, Subtitles } from "lucide-react";
import type { JobStatus, PipelineStep } from "@/types/job";

export interface PipelineStepConfig {
  key: PipelineStep;
  label: string;
  shortLabel: string;
  description: string;
  icon: LucideIcon;
  statuses: JobStatus[];
}

export const PIPELINE_STEPS: PipelineStepConfig[] = [
  {
    key: "transcribe",
    label: "Transcribe audio",
    shortLabel: "Transcribe",
    description: "Align narration to your script with Whisper",
    icon: Mic,
    statuses: ["transcribing", "pending"],
  },
  {
    key: "segment",
    label: "Segment scenes",
    shortLabel: "Scenes",
    description: "Break the script into timed visual scenes",
    icon: Clapperboard,
    statuses: ["segmenting"],
  },
  {
    key: "visuals",
    label: "Assemble visuals",
    shortLabel: "Visuals",
    description: "Attach images or clips to each scene",
    icon: Image,
    statuses: ["attaching_visuals"],
  },
  {
    key: "subtitles",
    label: "Generate subtitles",
    shortLabel: "Subtitles",
    description: "Build cinematic subtitle cues",
    icon: Subtitles,
    statuses: ["generating_subtitles"],
  },
  {
    key: "render",
    label: "Render video",
    shortLabel: "Render",
    description: "Compose and export the final MP4",
    icon: Film,
    statuses: ["rendering"],
  },
];

export function stepIndex(step: PipelineStep | null | undefined): number {
  if (!step) return -1;
  return PIPELINE_STEPS.findIndex((s) => s.key === step);
}

export function statusToStep(status: JobStatus): PipelineStep | null {
  const map: Record<JobStatus, PipelineStep | null> = {
    pending: "transcribe",
    transcribing: "transcribe",
    segmenting: "segment",
    attaching_visuals: "visuals",
    generating_subtitles: "subtitles",
    rendering: "render",
    completed: "render",
    failed: null,
  };
  return map[status] ?? null;
}

export function stepState(
  stepKey: PipelineStep,
  currentStep: PipelineStep | null | undefined,
  terminal: "completed" | "failed" | null,
): "upcoming" | "active" | "complete" | "failed" {
  const idx = stepIndex(stepKey);
  const currentIdx = stepIndex(currentStep);
  if (terminal === "failed" && currentStep === stepKey) return "failed";
  if (terminal === "completed") return "complete";
  if (currentIdx < 0) return idx === 0 ? "active" : "upcoming";
  if (idx < currentIdx) return "complete";
  if (idx === currentIdx) return "active";
  return "upcoming";
}

export const STATUS_LABELS: Record<JobStatus, string> = {
  pending: "Queued",
  transcribing: "Transcribing",
  segmenting: "Segmenting",
  attaching_visuals: "Visual assembly",
  generating_subtitles: "Subtitles",
  rendering: "Rendering",
  completed: "Complete",
  failed: "Failed",
};
