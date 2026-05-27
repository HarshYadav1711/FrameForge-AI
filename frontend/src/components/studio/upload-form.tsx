"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface UploadFormProps {
  disabled?: boolean;
  onSubmit: (script: string, audio: File) => Promise<void>;
}

export function UploadForm({ disabled, onSubmit }: UploadFormProps) {
  const [script, setScript] = useState("");
  const [audio, setAudio] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!script.trim() || script.trim().length < 10) {
      setError("Script must be at least 10 characters.");
      return;
    }
    if (!audio) {
      setError("Upload a narration audio file.");
      return;
    }

    try {
      await onSubmit(script.trim(), audio);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start job");
    }
  }

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
              className="resize-y min-h-[180px] font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <Label className="flex flex-col items-start gap-2">
              Narration audio
              <input
                ref={fileRef}
                id="audio"
                type="file"
                title="Narration audio"
                accept=".mp3,.wav,.m4a,.ogg,.flac,.webm,audio/*"
                className="block w-full text-sm text-muted-foreground file:mr-4 file:rounded-md file:border-0 file:bg-secondary file:px-4 file:py-2 file:text-sm file:font-medium file:text-secondary-foreground hover:file:bg-secondary/80"
                disabled={disabled}
                onChange={(e) => setAudio(e.target.files?.[0] ?? null)}
              />
            </Label>
            {audio && (
              <p className="text-xs text-muted-foreground">
                {audio.name} · {(audio.size / 1024 / 1024).toFixed(2)} MB
              </p>
            )}
          </div>

          {error && (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}

          <Button type="submit" size="lg" className="w-full" disabled={disabled}>
            Generate video
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
