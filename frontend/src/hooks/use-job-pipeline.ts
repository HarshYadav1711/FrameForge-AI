"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getJob } from "@/lib/api";
import { STATUS_LABELS } from "@/lib/pipeline-steps";
import type { JobStatusResponse, PipelineStep } from "@/types/job";

const POLL_MS = 1500;
const TERMINAL = new Set(["completed", "failed"]);
const MAX_LOG_ENTRIES = 80;

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

function createLogId(seq: { current: number }): string {
  seq.current += 1;
  return `log-${seq.current}`;
}

function appendLogsFromJob(
  job: JobStatusResponse,
  prev: ProcessingLogEntry[],
  seen: Set<string>,
  nextId: () => string,
): ProcessingLogEntry[] {
  const entries = [...prev];

  const push = (level: LogLevel, message: string, step?: PipelineStep | null) => {
    if (seen.has(message)) return;
    seen.add(message);
    entries.push({
      id: nextId(),
      at: formatTime(job.updated_at),
      level,
      message,
      step: step ?? job.progress.step,
    });
  };

  const statusLine = `${STATUS_LABELS[job.status]}${job.progress.message ? ` — ${job.progress.message}` : ""}`;
  push("info", statusLine, job.progress.step);

  const rp = job.metadata?.rendering_progress;
  if (rp?.message) {
    const encodeLine = `Encode [${rp.phase}]: ${rp.message}`;
    if (encodeLine !== statusLine) {
      push("info", encodeLine, "render");
    }
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

  return entries.slice(-MAX_LOG_ENTRIES);
}

/** Poll job status. Mount only while a job is active (e.g. `key={jobId}`). */
export function useJobPipeline(jobId: string) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [logs, setLogs] = useState<ProcessingLogEntry[]>(() => {
    const seq = { current: 0 };
    return [
      {
        id: createLogId(seq),
        at: formatTime(new Date().toISOString()),
        level: "info",
        message: "Job queued — starting pipeline",
        step: "transcribe",
      },
    ];
  });
  const [pollError, setPollError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const logSeq = useRef(1);
  const seenMessages = useRef(new Set<string>(["Job queued — starting pipeline"]));
  const lastStatus = useRef<string | null>(null);
  const lastStep = useRef<string | null>(null);
  const lastProgressMessage = useRef<string | null>(null);
  const lastWhisperKey = useRef<string | null>(null);
  const lastRenderKey = useRef<string | null>(null);

  const nextLogId = useCallback(() => createLogId(logSeq), []);

  const poll = useCallback(
    async (id: string) => {
      const data = await getJob(id);
      setJob(data);
      setPollError(null);

      const statusChanged = lastStatus.current !== data.status;
      const stepChanged = lastStep.current !== (data.progress.step ?? "");
      const progressMessageChanged =
        lastProgressMessage.current !== (data.progress.message ?? "");

      const tp = data.metadata?.transcription_progress;
      const whisperKey =
        tp?.segments_completed != null
          ? `${tp.segments_completed}:${tp.percent ?? 0}`
          : null;
      const whisperChanged = whisperKey !== lastWhisperKey.current;

      const rp = data.metadata?.rendering_progress;
      const renderKey = rp ? `${rp.phase}:${rp.percent}:${rp.message}` : null;
      const renderChanged = renderKey !== lastRenderKey.current;

      const shouldAppendLogs =
        statusChanged ||
        stepChanged ||
        progressMessageChanged ||
        whisperChanged ||
        renderChanged ||
        data.status === "completed" ||
        data.status === "failed";

      if (shouldAppendLogs) {
        setLogs((prev) =>
          appendLogsFromJob(data, prev, seenMessages.current, nextLogId),
        );
        lastStatus.current = data.status;
        lastStep.current = data.progress.step ?? "";
        lastProgressMessage.current = data.progress.message ?? "";
        lastWhisperKey.current = whisperKey;
        lastRenderKey.current = renderKey;
      }

      return data;
    },
    [nextLogId],
  );

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

  return {
    job,
    logs,
    pollError,
    loading: loading && !job,
    processing,
    terminal,
    refresh: () => poll(jobId),
  };
}
