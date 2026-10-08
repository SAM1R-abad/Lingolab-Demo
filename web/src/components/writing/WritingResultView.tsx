"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { VocabularyDistributionChart } from "@/components/writing/VocabularyDistributionChart";
import { SpellingErrorList, GrammarErrorList } from "@/components/writing/ErrorLists";
import { RelevanceBadge } from "@/components/writing/RelevanceBadge";
import type { WritingSubmission } from "@/services/types";

export function WritingResultView({ submission }: { submission: WritingSubmission }) {
  const result = submission.result;
  if (!result) return null;

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader
          title="Overall estimate"
          description={`Based on ${result.word_count} words across ${result.sentence_count} sentences.`}
          action={
            <div className="flex items-center gap-2">
              <Badge tone="green" className="text-body">
                {result.overall_cefr_level}
              </Badge>
              <span className="text-caption capitalize text-text-secondary">{result.confidence} confidence</span>
            </div>
          }
        />
        {result.rationale && <p className="text-small text-text-secondary">{result.rationale}</p>}
        {result.feedback && <p className="mt-2 text-small text-text-primary">{result.feedback}</p>}
      </Card>

      {result.topic_relevance && (
        <Card>
          <CardHeader title="Topic relevance" description="How much of the picture your response covers." />
          <RelevanceBadge relevance={result.topic_relevance} details={result.topic_relevance_details} />
        </Card>
      )}

      <Card>
        <CardHeader
          title="Vocabulary (CEFR distribution)"
          description="Distribution of the CEFR level of individual words used - not an overall proficiency verdict."
        />
        <VocabularyDistributionChart
          distribution={result.vocabulary_distribution}
          dominantLevel={result.dominant_vocabulary_level}
        />
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <SpellingErrorList errors={submission.spelling_errors} />
        <GrammarErrorList errors={submission.grammar_errors} />
      </div>

      {(result.strengths.length > 0 || result.weaknesses.length > 0) && (
        <div className="grid gap-6 md:grid-cols-2">
          {result.strengths.length > 0 && (
            <Card>
              <CardHeader title="Strengths" />
              <ul className="flex flex-col gap-1 text-small text-text-primary">
                {result.strengths.map((s, i) => (
                  <li key={i}>&bull; {s}</li>
                ))}
              </ul>
            </Card>
          )}
          {result.weaknesses.length > 0 && (
            <Card>
              <CardHeader title="Room to improve" />
              <ul className="flex flex-col gap-1 text-small text-text-primary">
                {result.weaknesses.map((s, i) => (
                  <li key={i}>&bull; {s}</li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}

      {result.limitations && <Alert tone="info">{result.limitations}</Alert>}
    </div>
  );
}
