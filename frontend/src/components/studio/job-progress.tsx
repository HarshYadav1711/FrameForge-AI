"use client";

import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ErrorState } from "@/components/ui/error-state";
import { STATUS_LABELS } from "@/lib/pipeline-steps";
import { cn } from "@/lib/utils";
import type { ProcessingLogEntry } from "@/hooks/use-job-pipeline";
import type { JobStatusResponse } from "@/types/job";
import { ActiveStepDetail, ProgressStepper } from "./progress-stepper";
import { ProcessingLogsPanel } from "./processing-logs";

interface JobProgressPanelProps {
  job: JobStatusResponse;
  logs: ProcessingLogEntry[];
  isProcessing: boolean;
  pollError?: string | null;
  onRetryPoll?: () => void;
}

export function JobProgressPanel({
  job,
  logs,
  isProcessing,
  pollError,
  onRetryPoll,
}: JobProgressPanelProps) {
  const isFailed = job.status === "failed";
  const isDone = job.status === "completed";

  return (
    <div className="space-y-5 animate-in fade-in duration-300">
      <div className="glass-panel rounded-2xl p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Pipeline</h2>
            <ActiveStepDetail
              step={job.progress.step}
              message={job.progress.message}
            />
          </div>
          <Badge
            variant={isFailed ? "destructive" : isDone ? "default" : "secondary"}
            className={isDone ? "bg-primary/20 text-primary hover:bg-primary/25" : ""}
          >
            {STATUS_LABELS[job.status]}
          </Badge>
        </div>

        <div className="mt-6 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Overall progress</span>
            <span className="font-medium tabular-nums">{job.progress.percent}%</span>
          </div>
          <Progress
            value={job.progress.percent}
            className={cn(
              "h-2 [&_[data-slot=progress-indicator]]:transition-all [&_[data-slot=progress-indicator]]:duration-500",
              isFailed && "[&_[data-slot=progress-indicator]]:bg-destructive",
              !isFailed && !isDone && "[&_[data-slot=progress-indicator]]:bg-primary",
            )}
          />
        </div>

        <div className="mt-8">
          <ProgressStepper job={job} />
        </div>

        {job.scenes_count != null && (
          <p className="mt-6 text-sm text-muted-foreground">
            {job.scenes_count} scene{job.scenes_count === 1 ? "" : "s"}
            {job.duration_seconds != null &&
              ` · ${job.duration_seconds.toFixed(1)}s narration`}
          </p>
        )}
      </div>

      <ProcessingLogsPanel logs={logs} isProcessing={isProcessing} />

      {pollError && (
        <ErrorState
          title="Connection interrupted"
          message={pollError}
          onRetry={onRetryPoll}
        />
      )}

      {isFailed && job.error && (
        <ErrorState title="Pipeline failed" message={job.error} />
      )}
    </div>
  );
}
