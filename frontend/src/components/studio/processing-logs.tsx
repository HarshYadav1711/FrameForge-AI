"use client";

import { useEffect, useRef } from "react";
import { Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ProcessingLogEntry } from "@/hooks/use-job-pipeline";
import styles from "./processing-logs.module.css";

interface ProcessingLogsPanelProps {
  logs: ProcessingLogEntry[];
  isProcessing: boolean;
  className?: string;
}

const LEVEL_STYLES: Record<ProcessingLogEntry["level"], string> = {
  info: "text-muted-foreground",
  success: "text-emerald-400/90",
  warn: "text-amber-400/90",
  error: "text-destructive",
};

export function ProcessingLogsPanel({
  logs,
  isProcessing,
  className,
}: ProcessingLogsPanelProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  return (
    <div className={cn("glass-panel overflow-hidden rounded-2xl", className)}>
      <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
        <div className="flex items-center gap-2">
          <Terminal className="size-4 text-primary" aria-hidden />
          <span className="text-sm font-medium">Processing log</span>
        </div>
        {isProcessing ? (
          <span className="flex items-center gap-1.5 text-xs text-primary">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary opacity-60" />
              <span className="relative inline-flex size-2 rounded-full bg-primary" />
            </span>
            Live
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">Idle</span>
        )}
      </div>
      <div
        className={cn(
          styles.logScroll,
          "max-h-[220px] overflow-y-auto bg-black/30 px-4 py-3 font-mono text-xs leading-relaxed",
        )}
        role="log"
        aria-live="polite"
        aria-relevant="additions"
      >
        {logs.length === 0 ? (
          <p className="text-muted-foreground">Waiting for pipeline events…</p>
        ) : (
          <ul className="space-y-1.5">
            {logs.map((entry) => (
              <li
                key={entry.id}
                className="flex gap-2 animate-in fade-in slide-in-from-bottom-1 duration-200"
              >
                <span className="shrink-0 tabular-nums text-muted-foreground/70">
                  {entry.at}
                </span>
                <span className={cn("min-w-0 break-words", LEVEL_STYLES[entry.level])}>
                  {entry.message}
                </span>
              </li>
            ))}
          </ul>
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
