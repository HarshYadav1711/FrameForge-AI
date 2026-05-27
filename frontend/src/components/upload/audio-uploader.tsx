"use client";

import { useEffect } from "react";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAudioUpload } from "@/hooks/use-audio-upload";
import { AudioDropzone } from "./audio-dropzone";
import { AudioPreview } from "./audio-preview";
import { UploadProgress } from "./upload-progress";

interface AudioUploaderProps {
  disabled?: boolean;
  onUploadIdChange?: (uploadId: string | null) => void;
}

export function AudioUploader({ disabled, onUploadIdChange }: AudioUploaderProps) {
  const {
    file,
    previewUrl,
    state,
    isReady,
    uploadId,
    selectFile,
    clear,
    retry,
  } = useAudioUpload();

  const busy = disabled || state.phase === "uploading" || state.phase === "validating";

  useEffect(() => {
    onUploadIdChange?.(isReady && uploadId ? uploadId : null);
  }, [isReady, uploadId, onUploadIdChange]);

  return (
    <div className="space-y-3">
      <AudioDropzone
        disabled={busy}
        hasFile={!!file}
        onFileSelected={(next) => void selectFile(next)}
      />

      {file && previewUrl && state.phase !== "error" && (
        <AudioPreview
          file={file}
          previewUrl={previewUrl}
          onRemove={clear}
          disabled={busy}
        />
      )}

      <UploadProgress phase={state.phase} progress={state.progress} />

      {state.phase === "error" && state.error && (
        <div
          className="flex flex-col gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3"
          role="alert"
        >
          <div className="flex items-start gap-2 text-sm text-destructive">
            <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
            <span>{state.error}</span>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={retry}>
            Try again
          </Button>
        </div>
      )}
    </div>
  );
}
