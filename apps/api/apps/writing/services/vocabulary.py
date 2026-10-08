"""
Vocabulary analysis: CEFR-level distribution of the words used in a
submission.

Data source: cefrpy (https://github.com/Maximax67/cefrpy), which combines
the CEFR-J Wordlist (Tono Laboratory, TUFS) for A1-B2 and the Octanove
Vocabulary Profile for C1-C2. Runs fully locally (SQLite bundled in the
package), no external calls.

Explicit limitations (always surfaced via WritingResult.limitations):
  - coverage is limited to the CEFR-J/Octanove wordlist - words missing from
    it (slang, rare terms, typos, proper nouns) are classified "unknown",
    never treated as an error;
  - a word's level is determined by lemma + part of speech, NOT by its
    specific sense in context - polysemous words get an averaged level, not
    the level of the sense actually used in the text;
  - prepositions, pronouns, function words, and stop words are deliberately
    excluded from the statistics (otherwise A1 words like "the"/"a" would
    dominate the distribution and make it meaningless).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from cefrpy import CEFRAnalyzer

from apps.writing.services.nlp import get_nlp

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Parts of speech that carry lexical weight and are meaningful to score by
# CEFR. Function-word POS tags (prepositions, conjunctions, articles,
# pronouns, particles) are deliberately excluded from "lexical complexity".
_CONTENT_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}


@dataclass(frozen=True)
class VocabularyAnalysis:
    distribution: dict[str, int]  # {"A1": 25, ..., "unknown": 5}
    dominant_level: str | None  # mode of `distribution`, excluding "unknown" - see module docstring
    lexical_complexity_level: str | None
    analyzed_word_count: int
    unknown_words: list[str] = field(default_factory=list)


def _dominant_level(distribution: dict[str, int]) -> str | None:
    """
    The single most frequent CEFR bucket in `distribution` ("unknown" is
    excluded - it isn't a CEFR level). This is deliberately NOT the same
    thing as `lexical_complexity_level` (a weighted average of word scores):
    e.g. a distribution of A1=42%, A2=35%, B1=18%, B2=5% has a dominant
    level of A1 even though the average score is higher. Both numbers are
    reported - see WritingResult.dominant_vocabulary_level vs
    WritingResult.lexical_complexity_level - so the frontend/consumer never
    conflates "most common word level" with "overall lexical complexity".
    A single B2/C1 word occurring once does not make it dominant.
    """
    counts = {level: distribution.get(level, 0) for level in CEFR_ORDER}
    if sum(counts.values()) == 0:
        return None
    return max(CEFR_ORDER, key=lambda level: counts[level])


@lru_cache(maxsize=1)
def _get_analyzer() -> CEFRAnalyzer:
    return CEFRAnalyzer()


def _level_to_score(level: str) -> int:
    return CEFR_ORDER.index(level) + 1  # A1=1 ... C2=6


def _score_to_level(score: float) -> str:
    index = round(score) - 1
    index = max(0, min(len(CEFR_ORDER) - 1, index))
    return CEFR_ORDER[index]


def analyze_vocabulary(text: str) -> VocabularyAnalysis:
    distribution = {level: 0 for level in CEFR_ORDER}
    distribution["unknown"] = 0

    if not text or not text.strip():
        return VocabularyAnalysis(
            distribution=distribution,
            dominant_level=None,
            lexical_complexity_level=None,
            analyzed_word_count=0,
        )

    nlp = get_nlp()
    analyzer = _get_analyzer()
    doc = nlp(text)

    scores: list[float] = []
    unknown_words: list[str] = []

    for token in doc:
        if token.is_space or token.is_punct or token.is_stop:
            continue
        if not token.is_alpha:
            continue
        if token.pos_ not in _CONTENT_POS:
            continue

        cefr_level = analyzer.get_word_pos_level_CEFR(token.lemma_.lower(), token.tag_)
        if cefr_level is None:
            # Fall back to the word's averaged level (no POS) before giving
            # up and calling it "unknown".
            cefr_level = analyzer.get_average_word_level_CEFR(token.lemma_.lower())

        if cefr_level is None:
            distribution["unknown"] += 1
            unknown_words.append(token.text)
            continue

        level_str = str(cefr_level)
        if level_str not in CEFR_ORDER:
            distribution["unknown"] += 1
            unknown_words.append(token.text)
            continue

        distribution[level_str] += 1
        scores.append(_level_to_score(level_str))

    lexical_complexity_level = _score_to_level(sum(scores) / len(scores)) if scores else None

    return VocabularyAnalysis(
        distribution=distribution,
        dominant_level=_dominant_level(distribution),
        lexical_complexity_level=lexical_complexity_level,
        analyzed_word_count=len(scores),
        unknown_words=unknown_words[:50],  # don't blow up the result on long texts
    )
