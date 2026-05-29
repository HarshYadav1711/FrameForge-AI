"use client";

import { useCallback, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { ALLOWED_AUDIO_ACCEPT } from "@/lib/audio-validation";

interface AudioDropzoneProps {
  disabled?: boolean;
  onFileSelected: (file: File) => void;
  hasFile: boolean;
}

export function AudioDropzone({
  disabled,
  onFileSelected,
  hasFile,
}: AudioDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      const file = files?.[0];
      if (file) onFileSelected(file);
    },
    [onFileSelected],
  );

  return (
    <div
      onDragEnter={(e) => {
        e.preventDefault();
        if (!disabled) setDragOver(true);
      }}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragOver(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setDragOver(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        if (!disabled) handleFiles(e.dataTransfer.files);
      }}
    >
      <label
        className={cn(
          "flex w-full cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors",
          dragOver
            ? "border-primary bg-primary/10 scale-[1.01] shadow-lg shadow-primary/10"
            : "border-white/10 bg-muted/10 hover:border-primary/40 hover:bg-muted/20",
          disabled && "pointer-events-none opacity-50",
          hasFile && "py-6",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          title="Narration audio"
          accept={ALLOWED_AUDIO_ACCEPT}
          className="sr-only"
          disabled={disabled}
          onChange={(e) => {
            handleFiles(e.target.files);
            e.target.value = "";
          }}
        />
        <Upload
          className={cn("mb-3 size-8 text-muted-foreground", dragOver && "text-primary")}
          aria-hidden
        />
        <span className="text-sm font-medium">
          {hasFile ? "Drop or click to replace" : "Drag & drop narration audio"}
        </span>
        <span className="mt-1 text-xs text-muted-foreground">
          MP3, WAV, or M4A · max 50 MB
        </span>
      </label>
    </div>
  );
}
