"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

export function useWritingTasks() {
  return useQuery({
    queryKey: ["writing", "tasks"],
    queryFn: api.writingTasks,
  });
}

export function useWritingTask(taskId: number) {
  return useQuery({
    queryKey: ["writing", "task", taskId],
    queryFn: () => api.writingTask(taskId),
    enabled: Number.isFinite(taskId),
  });
}

export function useWritingSubmissions() {
  return useQuery({
    queryKey: ["writing", "submissions"],
    queryFn: api.writingSubmissions,
  });
}

/**
 * Polls a submission until analysis finishes (status becomes "completed" or
 * "failed"). Mirrors the assessment flow's plain-fetch-plus-useState pattern
 * for the *creation* step (see app/dashboard/writing/[taskId]/page.tsx),
 * but polling specifically benefits from React Query's refetchInterval.
 */
export function useWritingSubmissionPolling(submissionId: number | null) {
  return useQuery({
    queryKey: ["writing", "submission", submissionId],
    queryFn: () => api.writingSubmission(submissionId as number),
    enabled: submissionId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "completed" || status === "failed" ? false : 1500;
    },
  });
}
