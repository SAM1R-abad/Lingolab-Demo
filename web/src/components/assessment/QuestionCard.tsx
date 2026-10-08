"use client";

import { useState } from "react";
import { Check, X, BookOpenText } from "lucide-react";
import { cn, splitReadingPrompt } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import type { SessionQuestion } from "@/services/types";

interface QuestionCardProps {
  sessionQuestion: SessionQuestion;
  index: number;
  total: number;
  onAnswer: (answer: string) => Promise<void>;
  isSubmitting: boolean;
}

export function QuestionCard({ sessionQuestion, index, total, onAnswer, isSubmitting }: QuestionCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const { question } = sessionQuestion;
  const alreadyAnswered = sessionQuestion.answered_at !== null;
  const { passage, question: questionText } = splitReadingPrompt(question.prompt);

  const handleSelect = async (option: string) => {
    if (alreadyAnswered || isSubmitting) return;
    setSelected(option);
    await onAnswer(option);
  };

  return (
    <div className="rounded-card border border-border bg-surface p-6 shadow-sm md:p-8">
      <p className="text-caption font-medium uppercase tracking-wide text-ku-green">
        Question {index + 1} of {total} · Level {question.level}
      </p>

      {passage && (
        <div className="mt-4 rounded-input border border-border bg-background p-4">
          <p className="mb-2 flex items-center gap-1.5 text-caption font-medium uppercase tracking-wide text-text-secondary">
            <BookOpenText className="h-3.5 w-3.5" aria-hidden="true" />
            Reading passage
          </p>
          <p className="whitespace-pre-line text-small leading-relaxed text-text-primary">{passage}</p>
        </div>
      )}

      <h2 className="mt-3 text-h3 text-text-primary">{questionText}</h2>

      <div className="mt-6 flex flex-col gap-3" role="radiogroup" aria-label="Answer options">
        {question.options.map((option) => {
          const isSelected = selected === option;
          return (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={isSelected}
              disabled={alreadyAnswered || isSubmitting}
              onClick={() => handleSelect(option)}
              className={cn(
                "flex items-center justify-between rounded-input border px-4 py-3 text-left text-body transition-colors",
                "disabled:cursor-not-allowed",
                isSelected
                  ? "border-ku-green bg-ku-soft-green/40 text-ku-dark-green"
                  : "border-border text-text-primary hover:border-ku-green hover:bg-background"
              )}
            >
              <span>{option}</span>
              {isSelected && (isSubmitting ? null : <Check className="h-4 w-4 text-ku-green" aria-hidden="true" />)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function BatchProgress({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2" aria-label={`Question ${current} of ${total} in this level`}>
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-1.5 flex-1 rounded-badge",
            i < current ? "bg-ku-green" : "bg-border"
          )}
        />
      ))}
    </div>
  );
}
