"use client";

import { useState } from "react";
import Link from "next/link";
import { TrendingUp, ClipboardList, PenLine } from "lucide-react";
import { useSessions } from "@/hooks/useAssessment";
import { useWritingSubmissions } from "@/hooks/useWriting";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { FullPageSpinner, ErrorState, Spinner } from "@/components/ui/feedback";
import { EmptyState } from "@/components/ui/EmptyState";
import { cn } from "@/lib/utils";
import type { Skill } from "@/services/types";

const FILTERS: { value: Skill | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "vocabulary", label: "Vocabulary" },
  { value: "grammar", label: "Grammar" },
  { value: "reading", label: "Reading" },
];

export default function ProgressPage() {
  const { data: sessions, isLoading, isError, refetch } = useSessions();
  const {
    data: writingSubmissions,
    isLoading: isWritingLoading,
    isError: isWritingError,
    refetch: refetchWriting,
  } = useWritingSubmissions();
  const [filter, setFilter] = useState<Skill | "all">("all");

  if (isLoading) return <FullPageSpinner label="Loading your progress..." />;
  if (isError) return <ErrorState message="Could not load your progress." onRetry={() => refetch()} />;

  const filtered = (sessions ?? [])
    .filter((s) => filter === "all" || s.skill === filter)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  const bestBySkill = (skill: Skill) => {
    const completed = (sessions ?? []).filter((s) => s.skill === skill && s.status === "completed");
    if (completed.length === 0) return null;
    return completed.sort(
      (a, b) => new Date(b.completed_at || 0).getTime() - new Date(a.completed_at || 0).getTime()
    )[0].result_level;
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Progress</h1>
        <p className="mt-1 text-body text-text-secondary">
          Your CEFR level over time, per skill.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="flex items-center gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-input bg-ku-soft-green/50">
            <TrendingUp className="h-5 w-5 text-ku-dark-green" aria-hidden="true" />
          </div>
          <div>
            <p className="text-small text-text-secondary">Current vocabulary level</p>
            <p className="text-h3 text-text-primary">{bestBySkill("vocabulary") ?? "Not tested"}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-input bg-ku-light-blue/50">
            <TrendingUp className="h-5 w-5 text-ku-dark-green" aria-hidden="true" />
          </div>
          <div>
            <p className="text-small text-text-secondary">Current grammar level</p>
            <p className="text-h3 text-text-primary">{bestBySkill("grammar") ?? "Not tested"}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-input bg-ku-soft-green/50">
            <TrendingUp className="h-5 w-5 text-ku-dark-green" aria-hidden="true" />
          </div>
          <div>
            <p className="text-small text-text-secondary">Current reading level</p>
            <p className="text-h3 text-text-primary">{bestBySkill("reading") ?? "Not tested"}</p>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Test history" />

        <div className="mb-4 flex gap-2" role="tablist" aria-label="Filter by skill">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              role="tab"
              aria-selected={filter === f.value}
              onClick={() => setFilter(f.value)}
              className={cn(
                "rounded-badge px-3 py-1.5 text-small font-medium transition-colors",
                filter === f.value
                  ? "bg-ku-green text-white"
                  : "bg-background text-text-secondary hover:text-text-primary"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <EmptyState title="No sessions for this filter" description="Try a different skill filter, or start a new placement test." />
        ) : (
          <ul className="divide-y divide-border">
            {filtered.map((session) => (
              <li key={session.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
                <div className="flex items-center gap-3">
                  <ClipboardList className="h-4 w-4 text-text-secondary" aria-hidden="true" />
                  <div>
                    <p className="text-small font-medium capitalize text-text-primary">
                      {session.skill} placement test
                    </p>
                    <p className="text-caption text-text-secondary">
                      Started {new Date(session.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {session.status === "completed" ? (
                    <Badge tone="success">{session.result_level}</Badge>
                  ) : (
                    <Badge tone="warning">In progress · {session.current_level}</Badge>
                  )}
                  <Link
                    href={
                      session.status === "completed"
                        ? `/dashboard/assessment/${session.id}/result`
                        : `/dashboard/assessment/${session.id}`
                    }
                  >
                    <Button variant="ghost" size="sm">
                      {session.status === "completed" ? "View" : "Continue"}
                    </Button>
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <CardHeader
          title="Writing history"
          description="Your picture-description submissions and their results."
        />

        {isWritingLoading && (
          <div className="flex justify-center py-8">
            <Spinner className="h-6 w-6" />
          </div>
        )}

        {isWritingError && (
          <ErrorState message="Could not load your writing history." onRetry={() => refetchWriting()} />
        )}

        {!isWritingLoading && !isWritingError && (writingSubmissions?.length ?? 0) === 0 && (
          <EmptyState
            icon={PenLine}
            title="No writing submissions yet"
            description="Try a picture-description task to see your results here."
            actionLabel="Go to Writing"
            onAction={() => {
              window.location.href = "/dashboard/writing";
            }}
          />
        )}

        {writingSubmissions && writingSubmissions.length > 0 && (
          <ul className="divide-y divide-border">
            {writingSubmissions.map((submission) => (
              <li key={submission.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
                <div className="flex items-center gap-3">
                  <PenLine className="h-4 w-4 text-text-secondary" aria-hidden="true" />
                  <div>
                    <p className="text-small font-medium text-text-primary">{submission.task_title}</p>
                    <p className="text-caption text-text-secondary">
                      Submitted {new Date(submission.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {submission.status === "completed" && submission.overall_cefr_level ? (
                    <Badge tone="success">{submission.overall_cefr_level}</Badge>
                  ) : submission.status === "failed" ? (
                    <Badge tone="danger">Failed</Badge>
                  ) : (
                    <Badge tone="warning" className="capitalize">
                      {submission.status}
                    </Badge>
                  )}
                  <Link href={`/dashboard/writing/submission/${submission.id}`}>
                    <Button variant="ghost" size="sm">
                      View
                    </Button>
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
