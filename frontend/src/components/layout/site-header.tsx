import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="group flex items-center gap-2 text-sm font-semibold tracking-tight"
        >
          <span className="flex size-7 items-center justify-center rounded-lg bg-primary/20 text-xs font-bold text-primary transition-colors group-hover:bg-primary/30">
            FF
          </span>
          FrameForge
          <span className="text-primary">AI</span>
        </Link>
        <nav className="flex items-center gap-2 text-sm">
          <Link
            href="/"
            className="hidden rounded-md px-3 py-1.5 text-muted-foreground transition-colors hover:text-foreground sm:inline"
          >
            Home
          </Link>
          <Link href="/studio" className={cn(buttonVariants({ size: "sm" }))}>
            Open studio
          </Link>
        </nav>
      </div>
    </header>
  );
}
