"""
Persists a WritingAnalysisResult into Django models. Kept separate from
pipeline.py so the analysis itself stays ORM-free and testable/reusable
without a database.
"""

from __future__ import annotations

from django.db import transaction

from apps.writing.models import (
    GrammarError,
    SpellingError,
    WritingResult,
    WritingSubmission,
)
from apps.writing.services.pipeline import WritingAnalysisResult


@transaction.atomic
def persist_analysis_result(
    submission: WritingSubmission, analysis: WritingAnalysisResult
) -> WritingResult:
    result = WritingResult.objects.create(
        submission=submission,
        overall_score=analysis.overall_score,
        overall_cefr_level=analysis.overall_cefr_level,
        confidence=analysis.confidence,
        rationale=analysis.rationale,
        word_count=analysis.word_count,
        sentence_count=analysis.sentence_count,
        vocabulary_distribution=analysis.vocabulary_distribution,
        dominant_vocabulary_level=analysis.dominant_vocabulary_level,
        lexical_complexity_level=analysis.lexical_complexity_level,
        grammar_accuracy_level=analysis.grammar_accuracy_level,
        grammar_complexity_level=analysis.grammar_complexity_level,
        topic_relevance=analysis.topic_relevance,
        topic_relevance_details=analysis.topic_relevance_details,
        strengths=analysis.strengths,
        weaknesses=analysis.weaknesses,
        feedback=analysis.feedback,
        limitations=analysis.limitations,
    )

    SpellingError.objects.bulk_create(
        [
            SpellingError(
                submission=submission,
                word=issue.word,
                suggestion=issue.suggestion,
                error_type=issue.error_type,
                start_offset=issue.start_offset,
                end_offset=issue.end_offset,
            )
            for issue in analysis.spelling_issues
        ]
    )

    GrammarError.objects.bulk_create(
        [
            GrammarError(
                submission=submission,
                fragment=issue.fragment,
                suggestion=issue.suggestion,
                short_description=issue.short_description,
                rule_id=issue.rule_id,
                category=issue.category,
                start_offset=issue.start_offset,
                end_offset=issue.end_offset,
            )
            for issue in analysis.grammar_issues
        ]
    )

    return result
