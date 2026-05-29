"use client";

import { useState } from "react";
import { Loader2, Video } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/ui/error-state";
import { AudioUploader } from "@/components/upload/audio-uploader";

interface UploadFormProps {
  disabled?: boolean;
  submitError?: string | null;
  onSubmit: (script: string, uploadId: string) => Promise<void>;
}

export function UploadForm({ disabled, submitError, onSubmit }: UploadFormProps) {
  const [script, setScript] = useState("");
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!script.trim() || script.trim().length < 10) {
      setError("Script must be at least 10 characters.");
      return;
    }
    if (!uploadId) {
      setError("Upload narration audio before generating.");
      return;
    }

    try {
      await onSubmit(script.trim(), uploadId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start job");
    }
  }

  const displayError = error ?? submitError;
  const canSubmit = !!uploadId && !disabled;

  return (
    <Card className="glass-panel border-0 shadow-none">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
            <Video className="size-5" aria-hidden />
          </div>
          <div>
            <CardTitle className="text-xl">New project</CardTitle>
            <CardDescription className="mt-0.5">
              Audio + script in — finished video out.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="script" className="text-muted-foreground">
              Narration script
            </Label>
            <Textarea
              id="script"
              placeholder="Paste your full narration script here. We'll align it with the audio and break it into scenes…"
              rows={10}
              value={script}
              onChange={(e) => setScript(e.target.value)}
              disabled={disabled}
              className="min-h-[200px] resize-y border-input/80 bg-background/50 font-mono text-sm leading-relaxed focus-visible:ring-primary/40"
            />
            <p className="text-xs text-muted-foreground">
              {script.trim().length} characters
              {script.trim().length > 0 && script.trim().length < 10
                ? " · need at least 10"
                : ""}
            </p>
          </div>

          <div className="space-y-2">
            <Label className="text-muted-foreground">Narration audio</Label>
            <AudioUploader disabled={disabled} onUploadIdChange={setUploadId} />
          </div>

          {displayError && (
            <ErrorState title="Could not start" message={displayError} />
          )}

          <Button
            type="submit"
            size="lg"
            className="w-full gap-2 transition-all hover:shadow-lg hover:shadow-primary/20"
            disabled={!canSubmit}
          >
            {disabled ? (
              <>
                <Loader2 className="size-4 animate-spin" aria-hidden />
                Starting pipeline…
              </>
            ) : (
              <>
                <Video className="size-4" aria-hidden />
                Generate video
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
