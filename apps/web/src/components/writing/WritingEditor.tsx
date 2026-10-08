"use client";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

function countWords(text: string): number {
  const trimmed = text.trim();
  return trimmed === "" ? 0 : trimmed.split(/\s+/).length;
}

export function WritingEditor({
  value,
  onChange,
  minWordCount,
  onSubmit,
  isSubmitting,
}: {
  value: string;
  onChange: (value: string) => void;
  minWordCount: number;
  onSubmit: () => void;
  isSubmitting: boolean;
}) {
  const wordCount = countWords(value);
  const belowMinimum = wordCount < minWordCount;

  return (
    <div className="flex flex-col gap-3">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={12}
        placeholder="Write your response here..."
        className={cn(
          "w-full resize-y rounded-input border border-border bg-surface p-4 text-body text-text-primary",
          "placeholder:text-text-secondary transition-colors focus:border-ku-green focus:outline-none"
        )}
        disabled={isSubmitting}
      />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span
          className={cn(
            "text-small",
            belowMinimum ? "text-text-secondary" : "text-ku-green font-medium"
          )}
        >
          {wordCount} / {minWordCount} words
        </span>
        <Button onClick={onSubmit} isLoading={isSubmitting} disabled={wordCount === 0}>
          Submit for analysis
        </Button>
      </div>
    </div>
  );
}
