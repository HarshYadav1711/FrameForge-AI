import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-white/[0.06] py-10">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 text-center sm:flex-row sm:px-6 sm:text-left lg:px-8">
        <p className="text-xs text-muted-foreground">
          FrameForge AI — local-first video automation
        </p>
        <nav className="flex gap-6 text-xs text-muted-foreground">
          <Link href="/studio" className="transition-colors hover:text-foreground">
            Studio
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-foreground"
          >
            API
          </a>
        </nav>
      </div>
    </footer>
  );
}
