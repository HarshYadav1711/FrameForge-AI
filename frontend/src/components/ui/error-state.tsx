import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-2xl border border-destructive/25 bg-destructive/5 p-6",
        className,
      )}
    >
      <div className="flex gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-destructive/15 text-destructive">
          <AlertCircle className="size-5" aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-medium text-destructive">{title}</h3>
          <p className="mt-1 text-sm leading-relaxed text-destructive/90">{message}</p>
          {onRetry ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="mt-4 border-destructive/30 hover:bg-destructive/10"
              onClick={onRetry}
            >
              <RefreshCw className="size-3.5" aria-hidden />
              Try again
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
