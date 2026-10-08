"use client";

import { useEffect } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Save, X } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import type { AdminQuestion, AdminQuestionPayload, CEFRLevel, Skill } from "@/services/types";

const optionSchema = z.object({ value: z.string().min(1, "Required") });

const questionSchema = z
  .object({
    external_id: z.string().min(1, "Required"),
    skill: z.enum(["vocabulary", "grammar", "reading"]),
    level: z.enum(["A1", "A2", "B1", "B2", "C1", "C2"]),
    question_type: z.string().min(1, "Required"),
    prompt: z.string().min(1, "Required"),
    options: z.array(optionSchema).length(4),
    correctIndex: z.coerce.number().min(0).max(3),
    tag: z.string().optional(),
  })
  .refine((data) => new Set(data.options.map((o) => o.value)).size === 4, {
    message: "Options must be unique",
    path: ["options"],
  });

type FormValues = z.infer<typeof questionSchema>;

const SKILLS: Skill[] = ["vocabulary", "grammar", "reading"];
const LEVELS: CEFRLevel[] = ["A1", "A2", "B1", "B2", "C1", "C2"];

export function QuestionForm({
  initial,
  onSubmit,
  onCancel,
  isSaving,
}: {
  initial?: AdminQuestion | null;
  onSubmit: (payload: AdminQuestionPayload) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
}) {
  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(questionSchema),
    defaultValues: {
      external_id: "",
      skill: "vocabulary",
      level: "A1",
      question_type: "meaning",
      prompt: "",
      options: [{ value: "" }, { value: "" }, { value: "" }, { value: "" }],
      correctIndex: 0,
      tag: "",
    },
  });
  const { fields } = useFieldArray({ control, name: "options" });

  useEffect(() => {
    if (initial) {
      const correctIndex = Math.max(0, initial.options.indexOf(initial.correct_answer));
      reset({
        external_id: initial.external_id,
        skill: initial.skill,
        level: initial.level,
        question_type: initial.question_type,
        prompt: initial.prompt,
        options: initial.options.map((value) => ({ value })),
        correctIndex,
        tag: initial.tag ?? "",
      });
    }
  }, [initial, reset]);

  const submit = async (values: FormValues) => {
    const options = values.options.map((o) => o.value);
    await onSubmit({
      external_id: values.external_id,
      skill: values.skill,
      level: values.level,
      question_type: values.question_type,
      prompt: values.prompt,
      options,
      correct_answer: options[values.correctIndex],
      tag: values.tag,
    });
  };

  return (
    <Card>
      <CardHeader
        title={initial ? "Edit question" : "New question"}
        action={
          <button
            type="button"
            onClick={onCancel}
            className="rounded-input p-1.5 text-text-secondary hover:bg-background"
            aria-label="Close form"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        }
      />
      <form onSubmit={handleSubmit(submit)} noValidate className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="External ID" placeholder="e.g. A1-042" error={errors.external_id?.message} {...register("external_id")} />
          <Input label="Tag (word / grammar point)" {...register("tag")} />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="flex flex-col gap-1">
            <label className="text-small font-medium text-text-primary">Skill</label>
            <select
              className="h-11 rounded-input border border-border bg-surface px-3 text-body text-text-primary focus:border-ku-green"
              {...register("skill")}
            >
              {SKILLS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-small font-medium text-text-primary">Level</label>
            <select
              className="h-11 rounded-input border border-border bg-surface px-3 text-body text-text-primary focus:border-ku-green"
              {...register("level")}
            >
              {LEVELS.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </div>
          <Input label="Question type" placeholder="meaning / grammar" {...register("question_type")} />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-small font-medium text-text-primary">Prompt</label>
          <textarea
            rows={4}
            className="rounded-input border border-border bg-surface px-3 py-2 text-body text-text-primary focus:border-ku-green"
            {...register("prompt")}
          />
          {errors.prompt && <p className="text-caption text-danger">{errors.prompt.message}</p>}
          <p className="text-caption text-text-secondary">
            For Reading questions, put the passage and the comprehension question on separate
            lines, e.g. the passage first, a blank line, then the question.
          </p>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-small font-medium text-text-primary">
            Options (select the correct one)
          </label>
          {fields.map((field, i) => (
            <div key={field.id} className="flex items-center gap-3">
              <input type="radio" value={i} {...register("correctIndex")} className="h-4 w-4 accent-ku-green" />
              <Input
                className="flex-1"
                placeholder={`Option ${i + 1}`}
                error={errors.options?.[i]?.value?.message}
                {...register(`options.${i}.value` as const)}
              />
            </div>
          ))}
          {errors.options?.root && <p className="text-caption text-danger">{errors.options.root.message}</p>}
        </div>

        <div className="mt-2 flex gap-3">
          <Button type="submit" isLoading={isSaving}>
            <Save className="h-4 w-4" aria-hidden="true" />
            {initial ? "Save changes" : "Create question"}
          </Button>
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  );
}
