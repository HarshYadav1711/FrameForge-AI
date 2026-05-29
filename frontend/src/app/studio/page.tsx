import { Studio } from "@/components/studio/studio";

export default function StudioPage() {
  return (
    <div className="relative min-h-[calc(100vh-3.5rem)]">
      <div className="pointer-events-none absolute inset-0 studio-grid mesh-bg opacity-80" />
      <div className="relative mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-10 animate-in fade-in slide-in-from-top-2 duration-500">
          <p className="text-sm font-medium uppercase tracking-widest text-primary">
            Studio
          </p>
          <h1 className="mt-2 text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
            Create narrated video
          </h1>
          <p className="mt-3 max-w-2xl text-lg text-muted-foreground">
            Upload audio, paste your script, and let the pipeline handle transcription,
            scenes, visuals, subtitles, and render.
          </p>
        </header>
        <Studio />
      </div>
    </div>
  );
}
