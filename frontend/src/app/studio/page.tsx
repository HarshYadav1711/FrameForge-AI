import { Studio } from "@/components/studio/studio";

export default function StudioPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Studio</h1>
        <p className="mt-1 text-muted-foreground">
          Upload narration audio and your script to generate a video.
        </p>
      </div>
      <Studio />
    </div>
  );
}
