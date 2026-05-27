import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="text-sm font-semibold tracking-tight">
          FrameForge <span className="text-primary">AI</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link
            href="/studio"
            className={cn(buttonVariants({ size: "sm" }))}
          >
            Open studio
          </Link>
        </nav>
      </div>
    </header>
  );
}
