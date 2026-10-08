"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertTriangle, ArrowLeft } from "lucide-react";
import { useWritingSubmissionPolling } from "@/hooks/useWriting";
import { WritingResultView } from "@/components/writing/WritingResultView";
import { FullPageSpinner, ErrorState } from "@/components/ui/feedback";
import { Alert } from "@/components/ui/Alert";

export default function WritingSubmissionPage() {
  const params = useParams();
  const submissionId = Number(params.submissionId);

  const { data: submission, isLoading, isError, refetch } = useWritingSubmissionPolling(submissionId);

  if (isLoading && !submission) return <FullPageSpinner label="Loading your submission..." />;

  if (isError || !submission) {
    return (
      <div className="mx-auto max-w-2xl">
        <ErrorState message="Could not load this submission." onRetry={() => refetch()} />
      </div>
    );
  }

  if (submission.status === "pending" || submission.status === "processing") {
    return <FullPageSpinner label="Analyzing your writing (spelling, grammar, vocabulary, relevance)..." />;
  }

  if (submission.status === "failed") {
    return (
      <div className="mx-auto flex max-w-2xl flex-col gap-4">
        <Alert tone="danger">
          <span className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" />
            Analysis failed{submission.error_message ? `: ${submission.error_message}` : "."} Please try submitting
            again.
          </span>
        </Alert>
        <Link
          href={`/dashboard/writing/${submission.task.id}`}
          className="inline-flex items-center gap-1 text-small font-medium text-ku-green hover:underline"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to the task
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Link
        href="/dashboard/writing"
        className="inline-flex w-fit items-center gap-1 text-small font-medium text-ku-green hover:underline"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to Writing
      </Link>
      <div>
        <h1 className="text-h2 text-text-primary">{submission.task.title}</h1>
        <p className="mt-1 whitespace-pre-wrap text-small text-text-secondary">{submission.submitted_text}</p>
      </div>
      <WritingResultView submission={submission} />
    </div>
  );
}
