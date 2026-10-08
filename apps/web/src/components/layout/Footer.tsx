import { BookOpenCheck } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto flex max-w-desktop flex-col items-center justify-between gap-4 px-4 py-8 text-small text-text-secondary md:flex-row md:px-8">
        <div className="flex items-center gap-2 text-text-primary">
          <BookOpenCheck className="h-5 w-5 text-ku-green" aria-hidden="true" />
          <span className="font-medium">LingoLab</span>
        </div>
        <p>Karabakh University Excellence Center · Built on KUDS</p>
      </div>
    </footer>
  );
}
