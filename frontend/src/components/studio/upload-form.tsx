"use client";

import { useState } from "react";
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
import { AudioUploader } from "@/components/upload/audio-uploader";

interface UploadFormProps {
  disabled?: boolean;
  onSubmit: (script: string, uploadId: string) => Promise<void>;
}

export function UploadForm({ disabled, onSubmit }: UploadFormProps) {
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

  const canSubmit = !!uploadId && !disabled;

  return (
    <Card className="border-border/60 bg-card/80 backdrop-blur">
      <CardHeader>
        <CardTitle>New video</CardTitle>
        <CardDescription>
          Upload narration audio and paste your script. FrameForge handles the rest.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="script">Script</Label>
            <Textarea
              id="script"
              placeholder="Paste your full narration script here…"
              rows={10}
              value={script}
              onChange={(e) => setScript(e.target.value)}
              disabled={disabled}
              className="min-h-[180px] resize-y font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <Label>Narration audio</Label>
            <AudioUploader
              disabled={disabled}
              onUploadIdChange={setUploadId}
            />
          </div>

          {error && (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}

          <Button type="submit" size="lg" className="w-full" disabled={!canSubmit}>
            Generate video
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
