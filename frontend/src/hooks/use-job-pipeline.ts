"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getJob } from "@/lib/api";
import { STATUS_LABELS, stepIndex } from "@/lib/pipeline-steps";
import type { JobStatusResponse, PipelineStep } from "@/types/job";

const POLL_MS = 1500;
const TERMINAL = new Set(["completed", "failed"]);

export type LogLevel = "info" | "success" | "warn" | "error";

export interface ProcessingLogEntry {
  id: string;
  at: string;
  level: LogLevel;
  message: string;
  step?: PipelineStep | null;
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "";
  }
}

function initialLog(): ProcessingLogEntry[] {
  return [
    {
      id: "init",
      at: formatTime(new Date().toISOString()),
      level: "info",
      message: "Job queued — starting pipeline",
      step: "transcribe",
    },
  ];
}

function logsFromJob(
  job: JobStatusResponse,
  prev: ProcessingLogEntry[],
): ProcessingLogEntry[] {
  const entries = [...prev];
  const push = (level: LogLevel, message: string, step?: PipelineStep | null) => {
    const last = entries[entries.length - 1];
    if (last?.message === message) return;
    entries.push({
      id: `${job.updated_at}-${entries.length}-${message.slice(0, 24)}`,
      at: formatTime(job.updated_at),
      level,
      message,
      step: step ?? job.progress.step,
    });
  };

  const statusLine = `${STATUS_LABELS[job.status]}${job.progress.message ? ` — ${job.progress.message}` : ""}`;
  push("info", statusLine, job.progress.step);

  const rp = job.metadata?.rendering_progress;
  if (rp?.message && rp.message !== job.progress.message) {
    push("info", `Encode: ${rp.message}`, "render");
  }

  const tp = job.metadata?.transcription_progress;
  if (tp?.segments_completed != null && tp.segments_completed > 0) {
    push(
      "info",
      `Whisper: ${tp.segments_completed} segments (${tp.percent ?? 0}%)`,
      "transcribe",
    );
  }

  if (job.scenes_count != null && job.status !== "pending") {
    push("success", `Timeline: ${job.scenes_count} scenes`, "segment");
  }

  if (job.metadata?.render_output?.file_size_bytes) {
    const mb = (job.metadata.render_output.file_size_bytes / (1024 * 1024)).toFixed(1);
    push("success", `Export complete (${mb} MB)`, "render");
  }

  if (job.status === "failed" && job.error) {
    push("error", job.error, job.progress.step);
  }

  if (job.status === "completed") {
    push("success", "Video ready for preview", "render");
  }

  return entries.slice(-80);
}

/** Poll job status. Mount only while a job is active (e.g. `key={jobId}`). */
export function useJobPipeline(jobId: string) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [logs, setLogs] = useState<ProcessingLogEntry[]>(initialLog);
  const [pollError, setPollError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const lastStatus = useRef<string | null>(null);
  const lastStep = useRef<string | null>(null);

  const poll = useCallback(async (id: string) => {
    const data = await getJob(id);
    setJob(data);
    setPollError(null);

    const statusChanged = lastStatus.current !== data.status;
    const stepChanged = lastStep.current !== (data.progress.step ?? "");
    if (statusChanged || stepChanged || data.progress.message) {
      setLogs((prev) => logsFromJob(data, prev));
      lastStatus.current = data.status;
      lastStep.current = data.progress.step ?? "";
    }

    return data;
  }, []);

  useEffect(() => {
    let active = true;

    const tick = async () => {
      try {
        const data = await poll(jobId);
        if (!active) return;
        if (TERMINAL.has(data.status)) setLoading(false);
      } catch (err) {
        if (!active) return;
        setPollError(err instanceof Error ? err.message : "Could not reach API");
      } finally {
        if (active) setLoading(false);
      }
    };

    void tick();
    const interval = setInterval(() => void tick(), POLL_MS);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [jobId, poll]);

  const terminal =
    job?.status === "completed" ? "completed" : job?.status === "failed" ? "failed" : null;
  const processing = job != null && !TERMINAL.has(job.status);
  const currentStepIdx = stepIndex(job?.progress.step);

  return {
    job,
    logs,
    pollError,
    loading: loading && !job,
    processing,
    terminal,
    currentStepIdx,
    refresh: () => poll(jobId),
  };
}
