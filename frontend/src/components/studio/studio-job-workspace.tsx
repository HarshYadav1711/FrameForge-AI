"use client";

import { RotateCcw, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useJobPipeline } from "@/hooks/use-job-pipeline";
import { JobProgressPanel } from "./job-progress";
import { OutputPreview } from "./output-preview";

interface StudioJobWorkspaceProps {
  jobId: string;
  onReset: () => void;
}

export function StudioJobWorkspace({ jobId, onReset }: StudioJobWorkspaceProps) {
  const { job, logs, pollError, loading, processing, refresh } =
    useJobPipeline(jobId);

  const completed = job?.status === "completed";
  const failed = job?.status === "failed";
  const showProgress = loading || processing || completed || failed;

  return (
    <>
      <div className="space-y-6 lg:col-span-5">
        {showProgress && loading && !job && (
          <div className="glass-panel space-y-4 rounded-2xl p-6">
            <Skeleton className="h-6 w-40" />
            <Skeleton className="h-2 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        )}

        {showProgress && job && (
          <JobProgressPanel
            job={job}
            logs={logs}
            isProcessing={processing}
            pollError={pollError}
            onRetryPoll={refresh}
          />
        )}

        {(completed || failed) && (
          <Button
            variant="outline"
            onClick={onReset}
            className="w-full gap-2 border-border/80"
          >
            <RotateCcw className="size-4" aria-hidden />
            Create another video
          </Button>
        )}
      </div>

      <div className="lg:col-span-7">
        {completed && job && <OutputPreview jobId={jobId} job={job} />}

        {processing && (
          <EmptyState
            icon={Wand2}
            title="Crafting your video"
            description="We're transcribing, segmenting, assembling visuals, and rendering. This panel will show your preview when the pipeline completes."
            className="min-h-[320px] animate-in fade-in duration-500"
          />
        )}

        {failed && !completed && (
          <EmptyState
            icon={Wand2}
            title="No output generated"
            description="Fix the issue shown in the pipeline panel, then start a new job."
            className="min-h-[200px]"
          />
        )}
      </div>
    </>
  );
}
