"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Pencil, Trash2, BookOpen } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { FullPageSpinner, ErrorState, Spinner } from "@/components/ui/feedback";
import { EmptyState } from "@/components/ui/EmptyState";
import { ConfirmDialog, useConfirmDialog } from "@/components/ui/ConfirmDialog";
import { QuestionForm } from "@/components/assessment/QuestionForm";
import { api, ApiError } from "@/services/api";
import type { AdminQuestion, AdminQuestionPayload, CEFRLevel, Skill } from "@/services/types";

const SKILL_FILTERS: { value: Skill | "all"; label: string }[] = [
  { value: "all", label: "All skills" },
  { value: "vocabulary", label: "Vocabulary" },
  { value: "grammar", label: "Grammar" },
  { value: "reading", label: "Reading" },
];
const LEVEL_FILTERS: (CEFRLevel | "all")[] = ["all", "A1", "A2", "B1", "B2", "C1", "C2"];

export default function AdminQuestionsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const toast = useToast();

  const [questions, setQuestions] = useState<AdminQuestion[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [skillFilter, setSkillFilter] = useState<Skill | "all">("all");
  const [levelFilter, setLevelFilter] = useState<CEFRLevel | "all">("all");

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<AdminQuestion | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const deleteDialog = useConfirmDialog();
  const [pendingDelete, setPendingDelete] = useState<AdminQuestion | null>(null);

  useEffect(() => {
    if (!authLoading && user && user.role !== "admin") {
      toast.error("This page requires an admin account.");
      router.replace("/dashboard");
    }
  }, [authLoading, user, router, toast]);

  const load = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await api.adminQuestions({
        skill: skillFilter === "all" ? undefined : skillFilter,
        level: levelFilter === "all" ? undefined : levelFilter,
      });
      setQuestions(data);
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : "Could not load questions.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin") load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, skillFilter, levelFilter]);

  const handleCreateOrUpdate = async (payload: AdminQuestionPayload) => {
    setIsSaving(true);
    try {
      if (editing) {
        await api.adminUpdateQuestion(editing.id, payload);
        toast.success("Question updated.");
      } else {
        await api.adminCreateQuestion(payload);
        toast.success("Question created.");
      }
      setFormOpen(false);
      setEditing(null);
      load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not save this question.");
    } finally {
      setIsSaving(false);
    }
  };

  const confirmDelete = (q: AdminQuestion) => {
    setPendingDelete(q);
    deleteDialog.open();
  };

  const handleDelete = async () => {
    if (!pendingDelete) return;
    deleteDialog.setLoading(true);
    try {
      await api.adminDeleteQuestion(pendingDelete.id);
      toast.success("Question deleted.");
      deleteDialog.close();
      setPendingDelete(null);
      load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not delete this question.");
    } finally {
      deleteDialog.setLoading(false);
    }
  };

  if (authLoading || !user) return <FullPageSpinner label="Checking access..." />;
  if (user.role !== "admin") return null; // redirect already in flight

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-h2 text-text-primary">Question bank</h1>
          <p className="mt-1 text-body text-text-secondary">
            Admin content management - create, edit, or remove CEFR questions.
          </p>
        </div>
        {!formOpen && (
          <Button
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            New question
          </Button>
        )}
      </div>

      {formOpen && (
        <QuestionForm
          initial={editing}
          isSaving={isSaving}
          onSubmit={handleCreateOrUpdate}
          onCancel={() => {
            setFormOpen(false);
            setEditing(null);
          }}
        />
      )}

      <Card>
        <CardHeader
          title="All questions"
          action={
            <div className="flex flex-wrap gap-2">
              <select
                value={skillFilter}
                onChange={(e) => setSkillFilter(e.target.value as Skill | "all")}
                className="h-9 rounded-input border border-border bg-surface px-2 text-small text-text-primary"
              >
                {SKILL_FILTERS.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value as CEFRLevel | "all")}
                className="h-9 rounded-input border border-border bg-surface px-2 text-small text-text-primary"
              >
                {LEVEL_FILTERS.map((l) => (
                  <option key={l} value={l}>
                    {l === "all" ? "All levels" : l}
                  </option>
                ))}
              </select>
            </div>
          }
        />

        {isLoading ? (
          <div className="flex justify-center py-10">
            <Spinner className="h-7 w-7" />
          </div>
        ) : loadError ? (
          <ErrorState message={loadError} onRetry={load} />
        ) : !questions || questions.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No questions match these filters"
            description="Try a different skill/level filter, or create a new question."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-small">
              <thead>
                <tr className="border-b border-border text-caption text-text-secondary">
                  <th className="py-2 pr-4 font-medium">ID</th>
                  <th className="py-2 pr-4 font-medium">Skill / Level</th>
                  <th className="py-2 pr-4 font-medium">Prompt</th>
                  <th className="py-2 pr-4 font-medium">Tag</th>
                  <th className="py-2 pr-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {questions.map((q) => (
                  <tr key={q.id} className="border-b border-border last:border-0">
                    <td className="py-3 pr-4 font-mono text-caption text-text-secondary">{q.external_id}</td>
                    <td className="py-3 pr-4">
                      <div className="flex flex-col gap-1">
                        <Badge tone="green" className="w-fit capitalize">
                          {q.skill}
                        </Badge>
                        <span className="text-caption text-text-secondary">{q.level}</span>
                      </div>
                    </td>
                    <td className="max-w-xs truncate py-3 pr-4 text-text-primary">{q.prompt}</td>
                    <td className="py-3 pr-4 text-text-secondary">{q.tag || "—"}</td>
                    <td className="py-3 pr-4">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            setEditing(q);
                            setFormOpen(true);
                          }}
                          className="rounded-input p-2 text-text-secondary hover:bg-background hover:text-ku-green"
                          aria-label={`Edit ${q.external_id}`}
                        >
                          <Pencil className="h-4 w-4" aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          onClick={() => confirmDelete(q)}
                          className="rounded-input p-2 text-text-secondary hover:bg-background hover:text-danger"
                          aria-label={`Delete ${q.external_id}`}
                        >
                          <Trash2 className="h-4 w-4" aria-hidden="true" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <ConfirmDialog
        open={deleteDialog.isOpen}
        title="Delete this question?"
        description={
          pendingDelete
            ? `"${pendingDelete.prompt}" (${pendingDelete.external_id}) will be permanently removed.`
            : ""
        }
        confirmLabel="Delete question"
        isLoading={deleteDialog.isLoading}
        onConfirm={handleDelete}
        onCancel={deleteDialog.close}
      />
    </div>
  );
}
