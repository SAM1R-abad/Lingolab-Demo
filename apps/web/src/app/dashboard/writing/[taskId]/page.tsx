"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useWritingTask } from "@/hooks/useWriting";
import { WritingEditor } from "@/components/writing/WritingEditor";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { FullPageSpinner, ErrorState } from "@/components/ui/feedback";
import { api, ApiError } from "@/services/api";
import { useToast } from "@/hooks/useToast";

export default function WritingTaskPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const taskId = Number(params.taskId);

  const { data: task, isLoading, isError, refetch } = useWritingTask(taskId);
  const [text, setText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (isLoading) return <FullPageSpinner label="Loading the task..." />;
  if (isError || !task) {
    return (
      <div className="mx-auto max-w-2xl">
        <ErrorState message="Could not load this writing task." onRetry={() => refetch()} />
      </div>
    );
  }

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const submission = await api.submitWriting({ task_id: task.id, submitted_text: text });
      router.push(`/dashboard/writing/submission/${submission.id}`);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Could not submit your response. Please try again.";
      setError(message);
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Card>
        <CardHeader
          title={task.title}
          action={task.target_level ? <Badge tone="green">{task.target_level}</Badge> : undefined}
        />
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="flex aspect-[4/3] w-full shrink-0 items-center justify-center overflow-hidden rounded-input bg-background sm:w-56">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={task.svg_url}
              alt={`Illustration for the "${task.title}" writing task`}
              className="h-full w-full object-contain p-2"
            />
          </div>
          <p className="text-small text-text-secondary">{task.prompt}</p>
        </div>
      </Card>

      {error && <Alert tone="danger">{error}</Alert>}

      <WritingEditor
        value={text}
        onChange={setText}
        minWordCount={task.min_word_count}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}
