"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import type { GrammarError, SpellingError } from "@/services/types";

export function SpellingErrorList({ errors }: { errors: SpellingError[] }) {
  return (
    <Card>
      <CardHeader
        title="Spelling"
        description={
          errors.length === 0
            ? "No spelling issues were found."
            : `${errors.length} possible spelling issue${errors.length === 1 ? "" : "s"} found.`
        }
      />
      {errors.length > 0 && (
        <ul className="flex flex-col gap-2">
          {errors.map((err, i) => (
            <li key={i} className="flex flex-wrap items-baseline gap-2 rounded-input bg-background px-3 py-2 text-small">
              <span className="font-medium text-danger line-through">{err.word}</span>
              {err.suggestion && (
                <>
                  <span className="text-text-secondary">&rarr;</span>
                  <span className="font-medium text-ku-green">{err.suggestion}</span>
                </>
              )}
              {err.error_type && <span className="text-caption text-text-secondary">({err.error_type})</span>}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function GrammarErrorList({ errors }: { errors: GrammarError[] }) {
  return (
    <Card>
      <CardHeader
        title="Grammar"
        description={
          errors.length === 0
            ? "No grammar issues were found."
            : `${errors.length} possible grammar issue${errors.length === 1 ? "" : "s"} found.`
        }
      />
      {errors.length > 0 && (
        <ul className="flex flex-col gap-3">
          {errors.map((err, i) => (
            <li key={i} className="rounded-input bg-background px-3 py-2 text-small">
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="font-medium text-danger">{err.fragment}</span>
                {err.suggestion && (
                  <>
                    <span className="text-text-secondary">&rarr;</span>
                    <span className="font-medium text-ku-green">{err.suggestion}</span>
                  </>
                )}
              </div>
              {err.short_description && (
                <p className="mt-1 text-caption text-text-secondary">{err.short_description}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
