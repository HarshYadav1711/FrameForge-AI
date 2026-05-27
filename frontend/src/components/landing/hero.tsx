import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { HealthBadge } from "./health-badge";

const FEATURES = [
  {
    title: "Transcribe",
    description: "Faster-Whisper aligns narration to your script automatically.",
  },
  {
    title: "Scene breakdown",
    description: "Ollama segments your script into visual scenes with a local fallback.",
  },
  {
    title: "Render & export",
    description: "MoviePy composes visuals, subtitles, and audio into a downloadable MP4.",
  },
] as const;

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-border/60">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/15 via-background to-background" />
      <div className="relative mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
        <p className="text-sm font-medium uppercase tracking-widest text-primary">
          Production-oriented · Local-first
        </p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
          Turn narration into edited video — automatically
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-muted-foreground">
          Upload audio, paste your script, and let FrameForge transcribe, segment,
          attach visuals, generate subtitles, and render a finished MP4. Modular
          monolith. No credit card. No auth.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Link href="/studio" className={cn(buttonVariants({ size: "lg" }))}>
            Start creating
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
          >
            API docs
          </a>
        </div>
        <div className="mt-10">
          <HealthBadge />
        </div>
        <dl className="mt-16 grid gap-6 sm:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-border/60 bg-card/50 p-5 backdrop-blur"
            >
              <dt className="font-medium">{f.title}</dt>
              <dd className="mt-2 text-sm text-muted-foreground">{f.description}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
