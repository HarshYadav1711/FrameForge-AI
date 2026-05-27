"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { JobStatus, JobStatusResponse } from "@/types/job";

const STATUS_LABELS: Record<JobStatus, string> = {
  pending: "Queued",
  transcribing: "Transcribing",
  segmenting: "Segmenting scenes",
  attaching_visuals: "Generating visuals",
  generating_subtitles: "Building subtitles",
  rendering: "Rendering video",
  completed: "Complete",
  failed: "Failed",
};

const STEPS: { key: string; label: string }[] = [
  { key: "transcribe", label: "Transcribe" },
  { key: "segment", label: "Scenes" },
  { key: "visuals", label: "Visuals" },
  { key: "subtitles", label: "Subtitles" },
  { key: "render", label: "Render" },
];

interface JobProgressPanelProps {
  job: JobStatusResponse;
}

export function JobProgressPanel({ job }: JobProgressPanelProps) {
  const currentStep = job.progress.step;
  const isFailed = job.status === "failed";
  const isDone = job.status === "completed";

  return (
    <Card className="border-border/60 bg-card/80 backdrop-blur">
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle className="text-lg">Processing</CardTitle>
        <Badge variant={isFailed ? "destructive" : isDone ? "default" : "secondary"}>
          {STATUS_LABELS[job.status]}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              {job.progress.message || "Starting pipeline…"}
            </span>
            <span className="font-medium tabular-nums">{job.progress.percent}%</span>
          </div>
          <Progress value={job.progress.percent} className="h-2" />
        </div>

        <ol className="grid gap-2 sm:grid-cols-5">
          {STEPS.map((step) => {
            const idx = STEPS.findIndex((s) => s.key === currentStep);
            const stepIdx = STEPS.findIndex((s) => s.key === step.key);
            const active = currentStep === step.key;
            const done = isDone || (idx >= 0 && stepIdx < idx);

            return (
              <li
                key={step.key}
                className={`rounded-lg border px-3 py-2 text-center text-xs transition-colors ${
                  active
                    ? "border-primary bg-primary/10 text-primary"
                    : done
                      ? "border-border/80 text-foreground"
                      : "border-border/40 text-muted-foreground"
                }`}
              >
                {step.label}
              </li>
            );
          })}
        </ol>

        {job.scenes_count != null && (
          <p className="text-sm text-muted-foreground">
            {job.scenes_count} scene{job.scenes_count === 1 ? "" : "s"} ·{" "}
            {job.duration_seconds != null
              ? `${job.duration_seconds.toFixed(1)}s audio`
              : "duration pending"}
          </p>
        )}

        {isFailed && job.error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {job.error}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
