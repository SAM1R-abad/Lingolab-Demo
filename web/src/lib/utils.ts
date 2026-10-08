import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Reading questions store their passage and their actual question together
 * in `Question.prompt`, separated by this marker (see
 * `apps/api/apps/assessment/management/commands/import_questions.py`,
 * `READING_PASSAGE_SEPARATOR`). Vocabulary/grammar prompts never contain
 * this marker, so `splitReadingPrompt` is a no-op for them.
 */
const READING_PASSAGE_SEPARATOR = "\n\n[[READING_QUESTION]]\n\n";

export function splitReadingPrompt(prompt: string): { passage: string | null; question: string } {
  const idx = prompt.indexOf(READING_PASSAGE_SEPARATOR);
  if (idx === -1) {
    return { passage: null, question: prompt };
  }
  return {
    passage: prompt.slice(0, idx),
    question: prompt.slice(idx + READING_PASSAGE_SEPARATOR.length),
  };
}
