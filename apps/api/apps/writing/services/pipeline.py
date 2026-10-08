"""
Single entry point for analyzing a submission: runs spelling/grammar
checking, vocabulary analysis, grammar-complexity analysis, and topic-
relevance analysis, combines them into an overall assessment, and returns a
structure ready to be persisted (see services/persistence.py) and/or
serialized into an API response.

This module deliberately does not touch the Django ORM directly - it takes
plain values (submitted_text, target_level, expected_vocabulary) rather than
model instances, and persistence is handled separately, so the pipeline can
be unit-tested and reused outside Celery/Django if needed (e.g. a future
batch-analysis management command).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from apps.writing.services import relevance, scoring
from apps.writing.services.grammar_complexity import analyze_grammar_complexity
from apps.writing.services.language_check import (
    GrammarIssue,
    SpellingIssue,
    check_text,
)
from apps.writing.services.vocabulary import analyze_vocabulary

LIMITATIONS_TEXT = (
    "This assessment is generated automatically and is meant as a helper, "
    "not a certified CEFR exam. Spelling and grammar are checked by a "
    "rule-based tool (LanguageTool), which does not always account for "
    "meaning. Vocabulary level is determined against the CEFR-J/Octanove "
    "Vocabulary Profile wordlist - words outside that list are marked "
    "'unknown', not treated as an error. Grammatical construction "
    "complexity is estimated heuristically from syntactic parsing and may "
    "not match a more nuanced expert review. "
) + relevance.LIMITATIONS_TEXT


@dataclass(frozen=True)
class WritingAnalysisResult:
    word_count: int
    sentence_count: int

    spelling_issues: list[SpellingIssue]
    grammar_issues: list[GrammarIssue]

    vocabulary_distribution: dict[str, int]
    dominant_vocabulary_level: str | None
    lexical_complexity_level: str | None

    grammar_accuracy_level: str | None
    grammar_complexity_level: str | None

    overall_cefr_level: str
    overall_score: int
    confidence: str
    rationale: str

    topic_relevance: str | None
    topic_relevance_details: dict

    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    feedback: str = ""
    limitations: str = LIMITATIONS_TEXT


def _count_words_and_sentences(text: str) -> tuple[int, int]:
    from apps.writing.services.nlp import get_nlp

    if not text or not text.strip():
        return 0, 0

    nlp = get_nlp()
    doc = nlp(text)
    word_count = sum(1 for t in doc if t.is_alpha)
    sentence_count = sum(1 for _ in doc.sents)
    return word_count, sentence_count


def _build_feedback(overall_level: str, strengths: list[str], weaknesses: list[str]) -> str:
    strengths_part = " ".join(strengths[:2])
    weaknesses_part = " ".join(weaknesses[:2])
    return (
        f"Estimated writing level: {overall_level}. "
        f"Strengths: {strengths_part} "
        f"Room to improve: {weaknesses_part}"
    ).strip()


def analyze_writing(
    *,
    submitted_text: str,
    target_level: str | None = None,
    expected_vocabulary: list[dict] | None = None,
) -> WritingAnalysisResult:
    """
    Main analysis function. Synchronous and "heavy" (LanguageTool + spaCy +
    vocabulary analysis) - meant to be called from a Celery task, not
    directly from an HTTP view.
    """
    word_count, sentence_count = _count_words_and_sentences(submitted_text)

    language_result = check_text(submitted_text)
    vocabulary_result = analyze_vocabulary(submitted_text)
    complexity_result = analyze_grammar_complexity(submitted_text)
    relevance_result = relevance.analyze_relevance(
        submitted_text=submitted_text,
        expected_vocabulary=expected_vocabulary or [],
    )

    grammar_accuracy = scoring.grammar_accuracy_level(
        grammar_error_count=len(language_result.grammar_issues),
        word_count=word_count,
    )

    overall = scoring.compute_overall_assessment(
        lexical_complexity_level=vocabulary_result.lexical_complexity_level,
        grammar_accuracy_level=grammar_accuracy,
        grammar_complexity_level=complexity_result.complexity_level,
        word_count=word_count,
        target_level=target_level,
    )

    strengths, weaknesses = scoring.build_strengths_and_weaknesses(
        vocabulary_distribution=vocabulary_result.distribution,
        lexical_complexity_level=vocabulary_result.lexical_complexity_level,
        grammar_accuracy_level=grammar_accuracy,
        grammar_complexity_level=complexity_result.complexity_level,
        spelling_error_count=len(language_result.spelling_issues),
        grammar_error_count=len(language_result.grammar_issues),
        word_count=word_count,
    )

    feedback = _build_feedback(overall.cefr_level, strengths, weaknesses)

    topic_relevance = relevance_result.relevance if relevance_result else None
    topic_relevance_details = (
        {
            "matched_core_count": relevance_result.matched_core_count,
            "total_core_count": relevance_result.total_core_count,
            "matched_keywords": relevance_result.matched_keywords,
            "bonus_matches": relevance_result.bonus_matches,
        }
        if relevance_result
        else {}
    )

    return WritingAnalysisResult(
        word_count=word_count,
        sentence_count=sentence_count,
        spelling_issues=language_result.spelling_issues,
        grammar_issues=language_result.grammar_issues,
        vocabulary_distribution=vocabulary_result.distribution,
        dominant_vocabulary_level=vocabulary_result.dominant_level,
        lexical_complexity_level=vocabulary_result.lexical_complexity_level,
        grammar_accuracy_level=grammar_accuracy,
        grammar_complexity_level=complexity_result.complexity_level,
        overall_cefr_level=overall.cefr_level,
        overall_score=overall.score,
        confidence=overall.confidence,
        rationale=overall.rationale,
        topic_relevance=topic_relevance,
        topic_relevance_details=topic_relevance_details,
        strengths=strengths,
        weaknesses=weaknesses,
        feedback=feedback,
    )
