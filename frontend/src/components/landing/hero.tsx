import Link from "next/link";
import { ArrowRight, Clapperboard, Mic, Sparkles } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { HealthBadge } from "./health-badge";

const FEATURES = [
  {
    icon: Mic,
    title: "Transcribe & align",
    description:
      "Faster-Whisper maps narration to your script with word-level timing for scenes and subtitles.",
  },
  {
    icon: Clapperboard,
    title: "Intelligent scenes",
    description:
      "Local LLM segmentation breaks your script into timed scenes with visual prompts.",
  },
  {
    icon: Sparkles,
    title: "Render & deliver",
    description:
      "MoviePy composes visuals, cinematic subtitles, and audio into a stream-ready MP4.",
  },
] as const;

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-white/[0.06]">
      <div className="pointer-events-none absolute inset-0 mesh-bg" />
      <div className="pointer-events-none absolute inset-0 studio-grid opacity-40" />
      <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          <span className="relative flex size-1.5">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex size-1.5 rounded-full bg-primary" />
          </span>
          Local-first · No API keys required
        </div>

        <h1 className="mt-8 max-w-4xl text-balance text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
          Turn narration into{" "}
          <span className="bg-gradient-to-r from-primary via-primary to-chart-2 bg-clip-text text-transparent">
            finished video
          </span>{" "}
          — automatically
        </h1>

        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground">
          FrameForge is an AI video pipeline for creators who want production workflow
          without cloud lock-in. Upload audio, paste your script, and download an edited
          MP4 with scenes, visuals, and subtitles.
        </p>

        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Link
            href="/studio"
            className={cn(buttonVariants({ size: "lg" }), "gap-2 glow-primary")}
          >
            Start creating
            <ArrowRight className="size-4" aria-hidden />
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

        <div className="mt-20 grid gap-5 sm:grid-cols-3">
          {FEATURES.map((f) => (
            <article
              key={f.title}
              className="glass-panel group rounded-2xl p-6 transition-transform duration-300 hover:-translate-y-0.5"
            >
              <div className="mb-4 flex size-11 items-center justify-center rounded-xl bg-primary/15 text-primary transition-colors group-hover:bg-primary/25">
                <f.icon className="size-5" aria-hidden />
              </div>
              <h2 className="font-medium tracking-tight">{f.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {f.description}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
