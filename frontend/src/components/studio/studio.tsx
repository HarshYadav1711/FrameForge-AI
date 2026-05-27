"use client";

import { useCallback, useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { createJob, getJob } from "@/lib/api";
import type { JobStatusResponse } from "@/types/job";
import { JobProgressPanel } from "./job-progress";
import { UploadForm } from "./upload-form";
import { VideoPreview } from "./video-preview";

const POLL_MS = 2000;
const TERMINAL = new Set(["completed", "failed"]);

export function Studio() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const poll = useCallback(async (id: string) => {
    const data = await getJob(id);
    setJob(data);
    return data;
  }, []);

  useEffect(() => {
    if (!jobId) return;
    let active = true;

    const tick = async () => {
      try {
        const data = await poll(jobId);
        if (!active || TERMINAL.has(data.status)) return;
      } catch {
        /* retry on next interval */
      }
    };

    tick();
    const interval = setInterval(tick, POLL_MS);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [jobId, poll]);

  async function handleSubmit(script: string, uploadId: string) {
    setSubmitting(true);
    try {
      const res = await createJob(script, uploadId);
      setJobId(res.id);
      setJob(null);
      await poll(res.id);
    } finally {
      setSubmitting(false);
    }
  }

  function reset() {
    setJobId(null);
    setJob(null);
  }

  const processing = jobId && job && !TERMINAL.has(job.status);
  const completed = job?.status === "completed";

  return (
    <div className="mx-auto grid w-full max-w-6xl gap-8 lg:grid-cols-2">
      <div className="space-y-6">
        {!jobId ? (
          <UploadForm disabled={submitting} onSubmit={handleSubmit} />
        ) : (
          <>
            {job && <JobProgressPanel job={job} />}
            {(completed || job?.status === "failed") && (
              <Button variant="outline" onClick={reset} className="w-full">
                Create another video
              </Button>
            )}
          </>
        )}
      </div>

      <div className="space-y-6">
        {completed && jobId && <VideoPreview jobId={jobId} />}
        {!jobId && (
          <Alert className="border-border/60 bg-muted/30">
            <AlertTitle>How it works</AlertTitle>
            <AlertDescription className="mt-2 space-y-2 text-muted-foreground">
              <p>1. Upload narration audio (MP3, WAV, M4A).</p>
              <p>2. Paste your script — we transcribe and align scenes.</p>
              <p>3. Ollama segments the script; visuals and subtitles are generated locally.</p>
              <p>4. Download your edited MP4 when processing finishes.</p>
            </AlertDescription>
          </Alert>
        )}
        {processing && (
          <p className="text-center text-sm text-muted-foreground lg:text-left">
            First run may take longer while Whisper loads the model.
          </p>
        )}
      </div>
    </div>
  );
}
