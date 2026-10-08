"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Award, RotateCcw, LayoutDashboard } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { FullPageSpinner, ErrorState, Spinner } from "@/components/ui/feedback";
import { api, ApiError } from "@/services/api";
import type { SessionResult } from "@/services/types";

// recharts is a sizeable dependency only needed on this one screen - load
// it on demand instead of shipping it in the shared dashboard bundle.
const LevelBreakdownChart = dynamic(
  () => import("@/components/assessment/LevelBreakdownChart").then((m) => m.LevelBreakdownChart),
  { ssr: false, loading: () => <div className="flex h-64 w-full items-center justify-center"><Spinner /></div> }
);

export default function AssessmentResultPage() {
  const params = useParams();
  const sessionId = Number(params.sessionId);

  const [result, setResult] = useState<SessionResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setIsLoading(true);
    setError(null);
    api
      .sessionResult(sessionId)
      .then(setResult)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not load this result.")
      )
      .finally(() => setIsLoading(false));
  }, [sessionId]);

  useEffect(() => {
    load();
  }, [load]);

  if (isLoading) return <FullPageSpinner label="Loading your result..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!result) return null;

  const isPreA1 = result.result_level === "Pre-A1";

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Card className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-ku-soft-green/50">
          <Award className="h-8 w-8 text-ku-dark-green" aria-hidden="true" />
        </div>
        <p className="mt-4 text-small capitalize text-text-secondary">{result.skill} placement test</p>
        <h1 className="mt-1 text-display text-ku-dark-green">{result.result_level}</h1>
        <p className="mt-2 text-body text-text-secondary">
          {isPreA1
            ? "Your score was below A1 threshold. Every learner starts somewhere - foundational material will help build up from here."
            : `You scored 80% or higher through level ${result.result_level}.`}
        </p>

        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {result.passed_levels.length === 0 && !isPreA1 && (
            <Badge tone="neutral">No levels passed yet</Badge>
          )}
          {result.passed_levels.map((level) => (
            <Badge key={level} tone="success">
              {level} passed
            </Badge>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Score by level"
          description="Each level needs 80% or higher to advance to the next."
        />
        <LevelBreakdownChart data={result.level_breakdown} />
      </Card>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Link href={`/dashboard/assessment?skill=${result.skill}`} className="flex-1">
          <Button variant="secondary" className="w-full">
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            Retake this test
          </Button>
        </Link>
        <Link href="/dashboard" className="flex-1">
          <Button className="w-full">
            <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
            Back to dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
}
