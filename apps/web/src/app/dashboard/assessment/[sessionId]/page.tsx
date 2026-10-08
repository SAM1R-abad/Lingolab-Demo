"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { TrendingUp } from "lucide-react";
import { QuestionCard, BatchProgress } from "@/components/assessment/QuestionCard";
import { FullPageSpinner, ErrorState } from "@/components/ui/feedback";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { api, ApiError } from "@/services/api";
import { useToast } from "@/hooks/useToast";
import type { PlacementSession, SessionQuestion } from "@/services/types";

export default function AssessmentSessionPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const sessionId = Number(params.sessionId);

  const [session, setSession] = useState<PlacementSession | null>(null);
  const [questions, setQuestions] = useState<SessionQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [justAdvancedTo, setJustAdvancedTo] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    try {
      const res = await api.sessionStatus(sessionId);
      if (res.session.status === "completed") {
        router.replace(`/dashboard/assessment/${sessionId}/result`);
        return;
      }
      setSession(res.session);
      setQuestions(res.questions);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load this test session.");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, router]);

  useEffect(() => {
    loadStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const currentQuestion = questions.find((q) => q.answered_at === null);
  const answeredInLevel = questions.filter((q) => q.answered_at !== null).length;

  const handleAnswer = async (answer: string) => {
    if (!currentQuestion) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await api.submitAnswer(sessionId, currentQuestion.question.id, answer);

      if (res.result) {
        router.push(`/dashboard/assessment/${sessionId}/result`);
        return;
      }

      const previousLevel = session?.current_level;
      setSession(res.session);
      setQuestions(res.questions ?? []);

      if (res.session.current_level !== previousLevel) {
        setJustAdvancedTo(res.session.current_level);
        setTimeout(() => setJustAdvancedTo(null), 3000);
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not submit your answer. Please try again.";
      setError(message);
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) return <FullPageSpinner label="Loading your test..." />;

  if (error && !currentQuestion) {
    return (
      <div className="mx-auto max-w-2xl">
        <ErrorState
          message={error}
          onRetry={() => {
            setIsLoading(true);
            setError(null);
            loadStatus();
          }}
        />
      </div>
    );
  }

  if (!session || !currentQuestion) {
    return <FullPageSpinner label="Preparing the next question..." />;
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <Badge tone="green" className="capitalize">
          {session.skill} · Level {session.current_level}
        </Badge>
        {justAdvancedTo && (
          <span className="flex items-center gap-1 text-small font-medium text-ku-green">
            <TrendingUp className="h-4 w-4" aria-hidden="true" />
            Level up! Now at {justAdvancedTo}
          </span>
        )}
      </div>

      <BatchProgress current={answeredInLevel} total={questions.length} />

      {error && <Alert tone="danger">{error}</Alert>}

      <QuestionCard
        key={currentQuestion.id}
        sessionQuestion={currentQuestion}
        index={answeredInLevel}
        total={questions.length}
        onAnswer={handleAnswer}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}
