"""
Topic-relevance analysis: how much of a WritingTask's "expected vocabulary"
(see apps/writing/data/answer_keys.json, its `usage_notes`) shows up in the
student's submission.

This module did NOT exist in the standalone writing_assessment prototype -
it is new, written specifically to use the answer_keys.json data supplied
in `writing materials.zip`, per the product brief (section 9-10: "possible
vocabulary/answers", not a mandatory checklist).

Deliberately a simple, explainable, demo-level heuristic - not a semantic
similarity model:
  - Only lexical overlap (lemma-level, case-insensitive) between the
    submission and the task's `expected_vocabulary` entries (object
    `name`/`synonyms`) is checked, plus optional bonus credit for
    `position`/`attributes`/`action` phrase mentions.
  - Per answer_keys.json's own usage_notes, an object with `count == 0` is
    an optional/inferred detail - it is included as bonus-only evidence and
    NEVER counted against the student for being absent.
  - A missing keyword is never treated as an error and never required: this
    only produces supporting evidence of topic relevance, not a checklist
    the student must complete or a correctness check.
  - Classification is 3 coarse bands (relevant / partially_relevant /
    weakly_relevant) - see TopicRelevance in models.py. This does not
    measure genuine semantic understanding of the picture, and the result
    always carries an explicit limitations note to that effect.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from apps.writing.services.nlp import get_nlp

LIMITATIONS_TEXT = (
    "Topic relevance is an approximate signal based on keyword/lemma overlap "
    "with a predefined list of objects expected in the picture. It does not "
    "measure true semantic understanding, does not require every keyword to "
    "be used, and a missing keyword is never treated as an error."
)

# Ratio of matched "core" objects (count > 0) needed to reach each band.
_RELEVANT_THRESHOLD = 0.5
_PARTIALLY_RELEVANT_THRESHOLD = 0.2


@dataclass(frozen=True)
class RelevanceAnalysis:
    relevance: str  # "relevant" / "partially_relevant" / "weakly_relevant"
    matched_core_count: int
    total_core_count: int
    matched_keywords: list[str]
    bonus_matches: list[str] = field(default_factory=list)
    limitations: str = LIMITATIONS_TEXT


def _lemma_set(text: str) -> set[str]:
    if not text or not text.strip():
        return set()
    nlp = get_nlp()
    doc = nlp(text)
    lemmas = {tok.lemma_.lower() for tok in doc if tok.is_alpha and not tok.is_stop}
    # Also keep raw lowercase tokens - some expected phrases (e.g. "front
    # door") won't lemmatize cleanly as single tokens, and a simple
    # substring check on the lowercase text is a reasonable fallback for
    # short multi-word phrases (position/attributes/action hints).
    return lemmas


def analyze_relevance(*, submitted_text: str, expected_vocabulary: list[dict]) -> RelevanceAnalysis | None:
    """
    `expected_vocabulary` is a WritingTask's list of scene objects, each
    shaped like the answer_keys.json entries:
    {"name": ..., "synonyms": [...], "count": int, "position": str,
     "attributes": [...], "action": str}.

    Returns None if the task has no expected_vocabulary configured (nothing
    to compare against - relevance simply isn't reported for that task).
    """
    if not expected_vocabulary:
        return None

    text_lower = (submitted_text or "").lower()
    text_lemmas = _lemma_set(submitted_text)

    def _mentioned(phrase: str) -> bool:
        phrase = (phrase or "").strip().lower()
        if not phrase:
            return False
        # Multi-word phrase: substring match on the raw lowercase text.
        if " " in phrase:
            return phrase in text_lower
        # Single word: match against lemmas (handles plurals/verb forms).
        return phrase in text_lemmas or phrase in text_lower

    core_objects = [obj for obj in expected_vocabulary if (obj.get("count") or 0) > 0]
    optional_objects = [obj for obj in expected_vocabulary if not (obj.get("count") or 0) > 0]

    matched_keywords: list[str] = []
    matched_core = 0
    for obj in core_objects:
        candidates = [obj.get("name", "")] + list(obj.get("synonyms", []) or [])
        if any(_mentioned(c) for c in candidates):
            matched_core += 1
            matched_keywords.append(obj.get("name", ""))

    bonus_matches: list[str] = []
    # Optional (count == 0) objects mentioned -> bonus evidence only.
    for obj in optional_objects:
        candidates = [obj.get("name", "")] + list(obj.get("synonyms", []) or [])
        if any(_mentioned(c) for c in candidates):
            bonus_matches.append(obj.get("name", ""))

    # Position / attributes / action -> bonus evidence of a richer,
    # on-topic description (per usage_notes: reward, never penalize).
    for obj in expected_vocabulary:
        if _mentioned(obj.get("position", "")):
            bonus_matches.append(f"position: {obj.get('name', '')}")
        for attr in obj.get("attributes", []) or []:
            if _mentioned(attr):
                bonus_matches.append(f"attribute: {attr}")
        if _mentioned(obj.get("action", "")):
            bonus_matches.append(f"action: {obj.get('name', '')}")

    total_core = len(core_objects)
    ratio = (matched_core / total_core) if total_core else 0.0

    if ratio >= _RELEVANT_THRESHOLD:
        relevance = "relevant"
    elif ratio >= _PARTIALLY_RELEVANT_THRESHOLD:
        relevance = "partially_relevant"
    else:
        relevance = "weakly_relevant"

    return RelevanceAnalysis(
        relevance=relevance,
        matched_core_count=matched_core,
        total_core_count=total_core,
        matched_keywords=matched_keywords,
        bonus_matches=bonus_matches[:30],  # keep the result bounded on long texts
    )
