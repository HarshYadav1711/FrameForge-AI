import { Loader2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import type { UploadPhase } from "@/types/upload";

interface UploadProgressProps {
  phase: UploadPhase;
  progress: number;
}

const LABELS: Record<UploadPhase, string> = {
  idle: "",
  validating: "Validating file…",
  uploading: "Uploading…",
  complete: "Upload complete",
  error: "",
};

export function UploadProgress({ phase, progress }: UploadProgressProps) {
  if (phase === "idle" || phase === "error") return null;

  const label = LABELS[phase];
  const showBar = phase === "uploading" || phase === "complete";

  return (
    <div className="space-y-2" role="status" aria-live="polite">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        {phase === "uploading" && (
          <Loader2 className="size-4 shrink-0 animate-spin" aria-hidden />
        )}
        <span>{label}</span>
        {showBar && (
          <span className="ml-auto tabular-nums font-medium text-foreground">
            {progress}%
          </span>
        )}
      </div>
      {showBar && <Progress value={progress} className="h-1.5" />}
    </div>
  );
}
