"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";
import { createJob } from "@/lib/api";
import { UploadForm } from "./upload-form";
import { StudioJobWorkspace } from "./studio-job-workspace";

export function Studio() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSubmit(script: string, uploadId: string) {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await createJob(script, uploadId);
      setJobId(res.id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to start job");
      throw err;
    } finally {
      setSubmitting(false);
    }
  }

  function reset() {
    setJobId(null);
    setSubmitError(null);
  }

  return (
    <div className="grid gap-8 lg:grid-cols-12 lg:gap-10">
      {!jobId ? (
        <>
          <div className="animate-in fade-in slide-in-from-left-4 duration-500 lg:col-span-5">
            <UploadForm
              disabled={submitting}
              onSubmit={handleSubmit}
              submitError={submitError}
            />
          </div>
          <div className="animate-in fade-in slide-in-from-right-4 duration-500 delay-150 lg:col-span-7">
            <EmptyState
              icon={Sparkles}
              title="Ready when you are"
              description="Upload narration audio and paste your script. FrameForge runs the full pipeline locally — transcription, scene breakdown, visuals, subtitles, and export."
              className="min-h-[360px]"
            >
              <ol className="mt-2 space-y-2 text-left text-sm text-muted-foreground">
                <li className="flex gap-2">
                  <span className="font-mono text-primary">1</span>
                  Upload MP3, WAV, or M4A narration
                </li>
                <li className="flex gap-2">
                  <span className="font-mono text-primary">2</span>
                  Paste your full script for alignment
                </li>
                <li className="flex gap-2">
                  <span className="font-mono text-primary">3</span>
                  Watch the pipeline run in real time
                </li>
                <li className="flex gap-2">
                  <span className="font-mono text-primary">4</span>
                  Preview and download your MP4
                </li>
              </ol>
            </EmptyState>
          </div>
        </>
      ) : (
        <StudioJobWorkspace key={jobId} jobId={jobId} onReset={reset} />
      )}
    </div>
  );
}
