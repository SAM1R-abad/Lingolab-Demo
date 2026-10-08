"""
Combines the independent signals (vocabulary / grammar accuracy / grammar
complexity / text length) into an overall CEFR estimate.

Explicit design decision: we do NOT count errors and assign a level directly
from that count. Instead:

  1. Each signal is independently mapped to an assumed CEFR level (or
     "not enough data").
  2. The overall level is a weighted blend of these levels, with tunable
     weights (see WEIGHTS below) - not a single "fewer errors = higher
     level" formula.
  3. If there are few signals (short text, some metrics couldn't be
     computed), confidence is lowered and surfaced to the frontend.

The thresholds below are a practical heuristic calibrated against general
CEFR descriptors (error density per 100 words), not the result of
statistical calibration on a labeled essay dataset. This is also stated
explicitly in the limitations text.

Topic relevance (services/relevance.py) is intentionally NOT one of the
weighted signals here: it measures whether the response addresses the given
picture/topic, not the student's English proficiency, so it must never by
itself move the overall CEFR estimate up or down. It is reported to the
frontend as an independent field.
"""

from __future__ import annotations

from dataclasses import dataclass

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Weights for the overall CEFR estimate. Accuracy matters more than the
# complexity of vocabulary/grammar used: a very "advanced" but inaccurate
# text is not considered advanced by CEFR.
WEIGHTS = {
    "grammar_accuracy": 0.4,
    "lexical_complexity": 0.3,
    "grammar_complexity": 0.3,
}

# Grammar-error density per 100 words -> assumed accuracy level. Fewer
# errors relative to text length maps to a higher level.
_GRAMMAR_ACCURACY_THRESHOLDS = [
    (2.0, "C2"),
    (4.0, "C1"),
    (7.0, "B2"),
    (12.0, "B1"),
    (20.0, "A2"),
]
_GRAMMAR_ACCURACY_FALLBACK = "A1"


def _level_to_score(level: str) -> int:
    return CEFR_ORDER.index(level) + 1


def _score_to_level(score: float) -> str:
    index = round(score) - 1
    index = max(0, min(len(CEFR_ORDER) - 1, index))
    return CEFR_ORDER[index]


def grammar_accuracy_level(grammar_error_count: int, word_count: int) -> str | None:
    if word_count == 0:
        return None
    errors_per_100_words = (grammar_error_count / word_count) * 100
    for threshold, level in _GRAMMAR_ACCURACY_THRESHOLDS:
        if errors_per_100_words <= threshold:
            return level
    return _GRAMMAR_ACCURACY_FALLBACK


@dataclass(frozen=True)
class OverallAssessment:
    cefr_level: str
    score: int  # 0-100, helper metric for the UI (progress bar etc.)
    confidence: str  # low / medium / high
    rationale: str


def compute_overall_assessment(
    *,
    lexical_complexity_level: str | None,
    grammar_accuracy_level: str | None,
    grammar_complexity_level: str | None,
    word_count: int,
    target_level: str | None,
) -> OverallAssessment:
    signals: dict[str, str] = {}
    if lexical_complexity_level:
        signals["lexical_complexity"] = lexical_complexity_level
    if grammar_accuracy_level:
        signals["grammar_accuracy"] = grammar_accuracy_level
    if grammar_complexity_level:
        signals["grammar_complexity"] = grammar_complexity_level

    if not signals:
        # Nothing to analyze (empty or extremely short text).
        return OverallAssessment(
            cefr_level="A1",
            score=0,
            confidence="low",
            rationale="The text is too short or empty - not enough data for an estimate.",
        )

    total_weight = sum(WEIGHTS[name] for name in signals)
    weighted_sum = sum(WEIGHTS[name] * _level_to_score(level) for name, level in signals.items())
    weighted_avg = weighted_sum / total_weight

    overall_level = _score_to_level(weighted_avg)
    # 0-100: linear scale from A1 (score=1) to C2 (score=6).
    score = round((weighted_avg - 1) / (len(CEFR_ORDER) - 1) * 100)
    score = max(0, min(100, score))

    # Confidence depends on how complete the signals are and text length.
    missing_signals = len(WEIGHTS) - len(signals)
    if word_count < 40 or missing_signals >= 2:
        confidence = "low"
    elif word_count < 100 or missing_signals == 1:
        confidence = "medium"
    else:
        confidence = "high"

    rationale_parts = []
    if "lexical_complexity" in signals:
        rationale_parts.append(f"vocabulary matches approximately {signals['lexical_complexity']}")
    if "grammar_accuracy" in signals:
        rationale_parts.append(f"grammatical accuracy matches approximately {signals['grammar_accuracy']}")
    if "grammar_complexity" in signals:
        rationale_parts.append(f"complexity of constructions used is approximately {signals['grammar_complexity']}")
    rationale = "The overall level is a weighted blend of signals: " + "; ".join(rationale_parts) + "."

    if target_level and target_level != overall_level:
        target_idx = _level_to_score(target_level)
        overall_idx = _level_to_score(overall_level)
        if overall_idx < target_idx:
            rationale += f" The task's target level is {target_level}; the text is currently below that bar."
        else:
            rationale += f" The text exceeds the task's target level ({target_level})."

    return OverallAssessment(
        cefr_level=overall_level,
        score=score,
        confidence=confidence,
        rationale=rationale,
    )


def build_strengths_and_weaknesses(
    *,
    vocabulary_distribution: dict[str, int],
    lexical_complexity_level: str | None,
    grammar_accuracy_level: str | None,
    grammar_complexity_level: str | None,
    spelling_error_count: int,
    grammar_error_count: int,
    word_count: int,
) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    weaknesses: list[str] = []

    advanced_words = vocabulary_distribution.get("B2", 0) + vocabulary_distribution.get("C1", 0) + vocabulary_distribution.get("C2", 0)
    if advanced_words >= 3:
        strengths.append(f"The text uses {advanced_words} words at B2 level or above.")

    if grammar_accuracy_level in {"C1", "C2"}:
        strengths.append("Low density of grammar errors relative to text length.")

    if grammar_complexity_level in {"B2", "C1", "C2"}:
        strengths.append("Varied grammatical constructions used (subordinate clauses, passive voice, conditionals).")

    if word_count > 0:
        spelling_ratio = spelling_error_count / word_count
        if spelling_ratio > 0.05:
            weaknesses.append("Elevated spelling error rate (more than 5% of words).")

        grammar_ratio = grammar_error_count / word_count
        if grammar_ratio > 0.1:
            weaknesses.append("High density of grammar errors relative to text length.")

    if grammar_complexity_level in {"A1", "A2"} and word_count >= 40:
        weaknesses.append("Mostly simple sentence structures without subordinate clauses.")

    if not strengths:
        strengths.append("The text is coherent, with no critical structural issues.")
    if not weaknesses:
        weaknesses.append("No significant weaknesses identified based on the available analysis signals.")

    return strengths, weaknesses
