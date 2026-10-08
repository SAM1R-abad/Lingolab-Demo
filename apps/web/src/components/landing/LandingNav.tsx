import Link from "next/link";
import { BookOpenCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function LandingNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface/90 backdrop-blur">
      <div className="mx-auto flex h-header max-w-desktop items-center justify-between px-4 md:px-8">
        <Link href="/" className="flex items-center gap-2 text-h4 font-semibold text-ku-dark-green">
          <BookOpenCheck className="h-6 w-6 text-ku-green" aria-hidden="true" />
          LingoLab
        </Link>
        <nav className="hidden items-center gap-6 md:flex">
          <a href="#pipeline" className="text-small text-text-secondary hover:text-text-primary">
            How it works
          </a>
          <a href="#modules" className="text-small text-text-secondary hover:text-text-primary">
            Modules
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">
              Log in
            </Button>
          </Link>
          <Link href="/signup">
            <Button size="sm">Get started</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
