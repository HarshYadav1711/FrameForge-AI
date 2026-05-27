import { Music2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatFileSize } from "@/lib/audio-validation";

interface AudioPreviewProps {
  file: File;
  previewUrl: string;
  onRemove: () => void;
  disabled?: boolean;
}

export function AudioPreview({
  file,
  previewUrl,
  onRemove,
  disabled,
}: AudioPreviewProps) {
  return (
    <div className="rounded-lg border border-border/60 bg-muted/20 p-4">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <Music2 className="size-4 shrink-0 text-primary" aria-hidden />
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{file.name}</p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(file.size)}
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          onClick={onRemove}
          disabled={disabled}
          aria-label="Remove audio"
        >
          <X className="size-4" />
        </Button>
      </div>
      <audio
        src={previewUrl}
        controls
        className="w-full"
        preload="metadata"
        aria-label={`Preview ${file.name}`}
      />
    </div>
  );
}
