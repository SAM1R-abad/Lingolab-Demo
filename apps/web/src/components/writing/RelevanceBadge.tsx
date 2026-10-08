"use client";

import { Badge } from "@/components/ui/Badge";
import type { TopicRelevance, TopicRelevanceDetails } from "@/services/types";

const RELEVANCE_LABEL: Record<TopicRelevance, string> = {
  relevant: "Relevant to the picture",
  partially_relevant: "Partially relevant to the picture",
  weakly_relevant: "Weakly relevant to the picture",
};

const RELEVANCE_TONE: Record<TopicRelevance, "green" | "cream" | "neutral"> = {
  relevant: "green",
  partially_relevant: "cream",
  weakly_relevant: "neutral",
};

export function RelevanceBadge({
  relevance,
  details,
}: {
  relevance: TopicRelevance | null;
  details: TopicRelevanceDetails;
}) {
  if (!relevance) return null;

  return (
    <div className="flex flex-col gap-2">
      <Badge tone={RELEVANCE_TONE[relevance]}>{RELEVANCE_LABEL[relevance]}</Badge>
      {typeof details.matched_core_count === "number" && typeof details.total_core_count === "number" && (
        <p className="text-caption text-text-secondary">
          Mentioned {details.matched_core_count} of {details.total_core_count} key elements from the picture.
          {details.matched_keywords && details.matched_keywords.length > 0 && (
            <> Matched: {details.matched_keywords.join(", ")}.</>
          )}
        </p>
      )}
    </div>
  );
}
