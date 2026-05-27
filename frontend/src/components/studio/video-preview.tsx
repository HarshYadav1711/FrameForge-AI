"use client";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { videoDownloadUrl } from "@/lib/api/jobs";

interface VideoPreviewProps {
  jobId: string;
}

export function VideoPreview({ jobId }: VideoPreviewProps) {
  const src = videoDownloadUrl(jobId);

  return (
    <Card className="border-border/60 bg-card/80 backdrop-blur">
      <CardHeader>
        <CardTitle>Your video</CardTitle>
        <CardDescription>Preview below or download the MP4.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-hidden rounded-xl border border-border/60 bg-black">
          <video
            src={src}
            controls
            className="aspect-video w-full"
            preload="metadata"
          />
        </div>
        <a
          href={src}
          download={`frameforge-${jobId.slice(0, 8)}.mp4`}
          className={cn(buttonVariants(), "inline-flex w-full sm:w-auto")}
        >
          Download MP4
        </a>
      </CardContent>
    </Card>
  );
}
