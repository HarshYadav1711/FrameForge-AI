"use client";

import { Check, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { PIPELINE_STEPS, stepState } from "@/lib/pipeline-steps";
import type { JobStatusResponse, PipelineStep } from "@/types/job";

interface ProgressStepperProps {
  job: JobStatusResponse;
  className?: string;
}

export function ProgressStepper({ job, className }: ProgressStepperProps) {
  const terminal =
    job.status === "completed" ? "completed" : job.status === "failed" ? "failed" : null;
  const currentStep = job.progress.step;

  return (
    <nav aria-label="Pipeline progress" className={cn("w-full", className)}>
      <ol className="relative flex flex-col gap-0 sm:flex-row sm:gap-0">
        {PIPELINE_STEPS.map((step, index) => {
          const state = stepState(step.key, currentStep, terminal);
          const Icon = step.icon;
          const isLast = index === PIPELINE_STEPS.length - 1;

          return (
            <li
              key={step.key}
              className={cn(
                "relative flex flex-1 flex-col sm:items-center",
                !isLast && "sm:pb-0",
              )}
            >
              {!isLast && (
                <span
                  className={cn(
                    "absolute left-[1.125rem] top-10 hidden h-[calc(100%-2rem)] w-px sm:left-1/2 sm:top-5 sm:block sm:h-px sm:w-full sm:-translate-x-1/2",
                    state === "complete" ? "bg-primary/50" : "bg-border",
                  )}
                  aria-hidden
                />
              )}
              <div className="relative z-10 flex items-start gap-3 sm:flex-col sm:items-center sm:gap-2 sm:px-2">
                <div
                  className={cn(
                    "flex size-9 shrink-0 items-center justify-center rounded-full border-2 transition-all duration-300",
                    state === "active" &&
                      "border-primary bg-primary/15 text-primary shadow-[0_0_24px_-4px] shadow-primary/40",
                    state === "complete" &&
                      "border-primary/60 bg-primary text-primary-foreground",
                    state === "failed" &&
                      "border-destructive bg-destructive/15 text-destructive",
                    state === "upcoming" &&
                      "border-border/80 bg-muted/40 text-muted-foreground",
                  )}
                >
                  {state === "active" ? (
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                  ) : state === "complete" ? (
                    <Check className="size-4" aria-hidden />
                  ) : state === "failed" ? (
                    <X className="size-4" aria-hidden />
                  ) : (
                    <Icon className="size-4" aria-hidden />
                  )}
                </div>
                <div className="min-w-0 pb-6 sm:pb-0 sm:text-center">
                  <p
                    className={cn(
                      "text-sm font-medium leading-tight",
                      state === "active" && "text-primary",
                      state === "upcoming" && "text-muted-foreground",
                    )}
                  >
                    {step.shortLabel}
                  </p>
                  <p className="mt-0.5 hidden text-xs text-muted-foreground sm:block">
                    {step.description}
                  </p>
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function ActiveStepDetail({
  step,
  message,
}: {
  step: PipelineStep | null;
  message: string;
}) {
  const config = PIPELINE_STEPS.find((s) => s.key === step);
  if (!config) return null;
  return (
    <p className="text-sm text-muted-foreground animate-in fade-in duration-300">
      <span className="font-medium text-foreground">{config.label}</span>
      {message ? ` — ${message}` : null}
    </p>
  );
}
