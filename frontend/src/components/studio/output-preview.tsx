"use client";

import { useState } from "react";
import { Download, Film, Sparkles } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { videoDownloadUrl } from "@/lib/api/jobs";
import type { JobStatusResponse } from "@/types/job";

interface OutputPreviewProps {
  jobId: string;
  job: JobStatusResponse;
}

function formatBytes(bytes: number | undefined): string {
  if (!bytes) return "—";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function OutputPreview({ jobId, job }: OutputPreviewProps) {
  const src = videoDownloadUrl(jobId);
  const [videoReady, setVideoReady] = useState(false);
  const output = job.metadata?.render_output;

  return (
    <section
      className="glass-panel glow-primary animate-in fade-in slide-in-from-bottom-4 overflow-hidden rounded-2xl duration-500"
      aria-label="Video output"
    >
      <div className="border-b border-white/[0.06] px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="size-4 text-primary" aria-hidden />
              <h2 className="text-lg font-semibold tracking-tight">Your video</h2>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              Preview the render or download the MP4.
            </p>
          </div>
          <a
            href={src}
            download={`frameforge-${jobId.slice(0, 8)}.mp4`}
            className={cn(buttonVariants({ size: "sm" }), "shrink-0 gap-1.5")}
          >
            <Download className="size-3.5" aria-hidden />
            Download
          </a>
        </div>
      </div>

      <div className="p-5">
        <div className="relative overflow-hidden rounded-xl border border-white/[0.08] bg-black shadow-inner">
          {!videoReady && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-black/80">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="aspect-video w-full max-w-md" />
            </div>
          )}
          <video
            src={src}
            controls
            playsInline
            className="aspect-video w-full"
            preload="metadata"
            onLoadedData={() => setVideoReady(true)}
          />
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <div className="rounded-lg bg-muted/30 px-3 py-2">
            <dt className="text-xs text-muted-foreground">Duration</dt>
            <dd className="mt-0.5 font-medium tabular-nums">
              {(() => {
                const rendered = output?.duration_seconds ?? 0;
                const seconds =
                  rendered > 0 ? rendered : (job.duration_seconds ?? 0);
                return seconds > 0 ? `${seconds.toFixed(1)}s` : "—";
              })()}
            </dd>
          </div>
          <div className="rounded-lg bg-muted/30 px-3 py-2">
            <dt className="text-xs text-muted-foreground">Resolution</dt>
            <dd className="mt-0.5 font-medium tabular-nums">
              {output?.width && output?.height
                ? `${output.width}×${output.height}`
                : "1920×1080"}
            </dd>
          </div>
          <div className="rounded-lg bg-muted/30 px-3 py-2">
            <dt className="text-xs text-muted-foreground">Scenes</dt>
            <dd className="mt-0.5 font-medium tabular-nums">
              {job.scenes_count ?? "—"}
            </dd>
          </div>
          <div className="rounded-lg bg-muted/30 px-3 py-2">
            <dt className="text-xs text-muted-foreground">File size</dt>
            <dd className="mt-0.5 font-medium tabular-nums">
              {formatBytes(output?.file_size_bytes)}
            </dd>
          </div>
        </dl>

        {output?.video_codec && (
          <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Film className="size-3.5" aria-hidden />
            {output.video_codec}
            {output.audio_codec ? ` + ${output.audio_codec}` : ""}
            {output.fps ? ` · ${output.fps} fps` : ""}
          </p>
        )}
      </div>
    </section>
  );
}
