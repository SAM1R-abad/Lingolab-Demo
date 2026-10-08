"use client";

import { PenLine } from "lucide-react";
import { useWritingTasks } from "@/hooks/useWriting";
import { TaskCard } from "@/components/writing/TaskCard";
import { Spinner, ErrorState } from "@/components/ui/feedback";
import { EmptyState } from "@/components/ui/EmptyState";

export default function WritingTasksPage() {
  const { data: tasks, isLoading, isError, refetch } = useWritingTasks();

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-h2 text-text-primary">Writing</h1>
        <p className="mt-1 text-body text-text-secondary">
          Pick a picture, describe what you see, and get feedback on spelling, grammar, vocabulary, and how well
          your response matches the picture.
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      )}

      {isError && <ErrorState message="Could not load writing tasks." onRetry={() => refetch()} />}

      {!isLoading && !isError && (tasks?.length ?? 0) === 0 && (
        <EmptyState
          icon={PenLine}
          title="No writing tasks available yet"
          description="Check back later - new picture-description tasks are added regularly."
        />
      )}

      {tasks && tasks.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
