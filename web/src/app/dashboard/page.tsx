"use client";

import Link from "next/link";
import { ClipboardList, TrendingUp, BookMarked, SpellCheck2, BookOpenText, PenLine, ArrowRight } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useSessions } from "@/hooks/useAssessment";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner, ErrorState } from "@/components/ui/feedback";
import { EmptyState } from "@/components/ui/EmptyState";
import type { PlacementSession, Skill } from "@/services/types";

function bestResultForSkill(sessions: PlacementSession[], skill: Skill) {
  const completed = sessions.filter((s) => s.skill === skill && s.status === "completed");
  if (completed.length === 0) return null;
  // Most recent completed session for that skill.
  return completed.sort(
    (a, b) => new Date(b.completed_at || 0).getTime() - new Date(a.completed_at || 0).getTime()
  )[0];
}

export default function DashboardHomePage() {
  const { user } = useAuth();
  const { data: sessions, isLoading, isError, refetch } = useSessions();

  const vocabResult = sessions ? bestResultForSkill(sessions, "vocabulary") : null;
  const grammarResult = sessions ? bestResultForSkill(sessions, "grammar") : null;
  const readingResult = sessions ? bestResultForSkill(sessions, "reading") : null;
  const inProgress = sessions?.filter((s) => s.status === "in_progress") ?? [];
  const recent = sessions
    ? [...sessions]
        .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
        .slice(0, 5)
    : [];

  return (
    <div className="flex flex-col gap-8">
      {/* Welcome Banner */}
      <div className="rounded-card bg-ku-green px-6 py-8 text-white md:px-8">
        <h1 className="text-h2 md:text-h1">Welcome back, {user?.username}.</h1>
        <p className="mt-2 max-w-xl text-body text-white/85">
          {vocabResult || grammarResult || readingResult
            ? "Here's where your English stands right now — and what to test next."
            : "Take your first adaptive placement test to see your CEFR level."}
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-input bg-ku-soft-green/50">
              <BookMarked className="h-5 w-5 text-ku-dark-green" aria-hidden="true" />
            </div>
            <div>
              <p className="text-h4 text-text-primary">Vocabulary test</p>
              <p className="text-caption text-text-secondary">CEFR-adaptive, A1 → C2</p>
            </div>
          </div>
          <Link href="/dashboard/assessment?skill=vocabulary">
            <Button size="sm">Start</Button>
          </Link>
        </Card>
        <Card className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-input bg-ku-light-blue/50">
              <SpellCheck2 className="h-5 w-5 text-ku-dark-green" aria-hidden="true" />
            </div>
            <div>
              <p className="text-h4 text-text-primary">Grammar test</p>
              <p className="text-caption text-text-secondary">CEFR-adaptive, A1 → C2</p>
            </div>
          </div>
          <Link href="/dashboard/assessment?skill=grammar">
            <Button size="sm">Start</Button>
          </Link>
        </Card>
        <Card className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-input bg-ku-soft-green/50">
              <BookOpenText className="h-5 w-5 text-ku-dark-green" aria-hidden="true" />
            </div>
            <div>
              <p className="text-h4 text-text-primary">Reading test</p>
              <p className="text-caption text-text-secondary">CEFR-adaptive, A1 → C2</p>
            </div>
          </div>
          <Link href="/dashboard/assessment?skill=reading">
            <Button size="sm">Start</Button>
          </Link>
        </Card>
        <Card className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-input bg-ku-light-blue/50">
              <PenLine className="h-5 w-5 text-ku-dark-green" aria-hidden="true" />
            </div>
            <div>
              <p className="text-h4 text-text-primary">Writing</p>
              <p className="text-caption text-text-secondary">Picture-description tasks</p>
            </div>
          </div>
          <Link href="/dashboard/writing">
            <Button size="sm">Start</Button>
          </Link>
        </Card>
      </div>

      {/* Statistics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Vocabulary level" value={vocabResult?.result_level ?? "Not tested"} />
        <StatCard label="Grammar level" value={grammarResult?.result_level ?? "Not tested"} />
        <StatCard label="Reading level" value={readingResult?.result_level ?? "Not tested"} />
        <StatCard label="Tests in progress" value={String(inProgress.length)} />
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader
          title="Recent activity"
          description="Your latest placement-test sessions."
          action={
            <Link href="/dashboard/progress" className="flex items-center gap-1 text-small font-medium text-ku-green hover:underline">
              View all
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          }
        />
        {isLoading ? (
          <div className="flex justify-center py-6">
            <Spinner />
          </div>
        ) : isError ? (
          <ErrorState message="Could not load your recent activity." onRetry={() => refetch()} />
        ) : recent.length === 0 ? (
          <EmptyState
            title="No sessions yet"
            description="Start a placement test above to see activity here."
          />
        ) : (
          <ul className="divide-y divide-border">
            {recent.map((session) => (
              <li key={session.id} className="flex items-center justify-between gap-4 py-3">
                <div className="flex items-center gap-3">
                  <ClipboardList className="h-4 w-4 text-text-secondary" aria-hidden="true" />
                  <div>
                    <p className="text-small font-medium capitalize text-text-primary">
                      {session.skill} placement test
                    </p>
                    <p className="text-caption text-text-secondary">
                      {session.status === "completed"
                        ? `Completed - ${session.result_level}`
                        : `In progress - level ${session.current_level}`}
                    </p>
                  </div>
                </div>
                <Link
                  href={
                    session.status === "completed"
                      ? `/dashboard/assessment/${session.id}/result`
                      : `/dashboard/assessment/${session.id}`
                  }
                >
                  <Button variant="ghost" size="sm">
                    {session.status === "completed" ? "View result" : "Continue"}
                  </Button>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <p className="text-small text-text-secondary">{label}</p>
      <div className="mt-2 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-ku-green" aria-hidden="true" />
        <span className="text-h2 text-text-primary">
          {value === "Not tested" ? <Badge tone="neutral">Not tested</Badge> : value}
        </span>
      </div>
    </Card>
  );
}
