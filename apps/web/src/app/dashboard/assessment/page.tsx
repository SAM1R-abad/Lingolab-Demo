"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { BookMarked, SpellCheck2, BookOpenText, Clock, Layers, Target } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { api, ApiError } from "@/services/api";
import type { Skill } from "@/services/types";
import { cn } from "@/lib/utils";

const SKILL_OPTIONS: {
  value: Skill;
  label: string;
  description: string;
  icon: typeof BookMarked;
}[] = [
  {
    value: "vocabulary",
    label: "Vocabulary",
    description: "Word meaning and usage across registers, from everyday to academic.",
    icon: BookMarked,
  },
  {
    value: "grammar",
    label: "Grammar",
    description: "Sentence structure, tenses, and forms from basic to advanced.",
    icon: SpellCheck2,
  },
  {
    value: "reading",
    label: "Reading",
    description: "Short passages with comprehension questions, from basic to advanced.",
    icon: BookOpenText,
  },
];

export default function AssessmentStartPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselected = searchParams.get("skill") as Skill | null;

  const [skill, setSkill] = useState<Skill>(
    preselected === "grammar" || preselected === "reading" ? preselected : "vocabulary"
  );
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async () => {
    setError(null);
    setIsStarting(true);
    try {
      const res = await api.startSession(skill);
      router.push(`/dashboard/assessment/${res.session.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start the test. Please try again.");
      setIsStarting(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Start a placement test</h1>
        <p className="mt-1 text-body text-text-secondary">
          Pick a skill. The test adapts as you answer, from A1 up to C2.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SKILL_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setSkill(option.value)}
            className={cn(
              "rounded-card border p-6 text-left transition-colors",
              skill === option.value
                ? "border-ku-green bg-ku-soft-green/30"
                : "border-border bg-surface hover:border-ku-green/50"
            )}
          >
            <option.icon className="h-6 w-6 text-ku-dark-green" aria-hidden="true" />
            <p className="mt-3 text-h4 text-text-primary">{option.label}</p>
            <p className="mt-1 text-small text-text-secondary">{option.description}</p>
          </button>
        ))}
      </div>

      <Card>
        <CardHeader title="What to expect" />
        <ul className="flex flex-col gap-3 text-small text-text-secondary">
          <li className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-ku-green" aria-hidden="true" />
            Starts at A1, with a short batch of questions per level.
          </li>
          <li className="flex items-center gap-2">
            <Target className="h-4 w-4 text-ku-green" aria-hidden="true" />
            Score 80% or higher on a level to move up to the next one.
          </li>
          <li className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-ku-green" aria-hidden="true" />
            Takes a few minutes. You'll see your result the moment it ends.
          </li>
        </ul>
      </Card>

      {error && <Alert tone="danger">{error}</Alert>}

      <Button size="lg" onClick={handleStart} isLoading={isStarting} className="w-full sm:w-auto">
        Start {skill} test
      </Button>
    </div>
  );
}
