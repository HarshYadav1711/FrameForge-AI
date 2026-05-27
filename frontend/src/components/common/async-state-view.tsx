"use client";

import { AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { AsyncState } from "@/lib/async-state";
import { isError, isLoading } from "@/lib/async-state";

interface AsyncStateViewProps<T> {
  state: AsyncState<T>;
  loadingMessage?: string;
  onRetry?: () => void;
  children: (data: T) => React.ReactNode;
}

export function AsyncStateView<T>({
  state,
  loadingMessage = "Loading…",
  onRetry,
  children,
}: AsyncStateViewProps<T>) {
  if (isLoading(state)) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground" role="status">
        <Loader2 className="size-4 animate-spin" aria-hidden />
        {loadingMessage}
      </div>
    );
  }

  if (isError(state)) {
    return (
      <div
        className="flex flex-col gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4"
        role="alert"
      >
        <div className="flex items-start gap-2 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
          <span>{state.error}</span>
        </div>
        {onRetry && (
          <Button type="button" variant="outline" size="sm" onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>
    );
  }

  if (state.data != null && state.status === "success") {
    return <>{children(state.data)}</>;
  }

  return null;
}
