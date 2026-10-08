"""
Scores the COMPLEXITY of the grammatical constructions used - separate
from their CORRECTNESS (that's services/language_check.py's job).

This is the most heuristic part of the analysis. Unlike vocabulary level,
where a ready-made labeled dataset exists (CEFR-J Wordlist), there is no
widely-accepted local tool that maps "construction X -> CEFR level". The
closest source is the CEFR-J Grammar Profile (Tono Lab), but that's a list
of grammar categories with levels, not a programmatic API - so this module
implements the mapping by hand via spaCy dependency parsing, over patterns
that CEFR practice consistently associates with particular learning stages.

This measures NOT the number of errors, but the variety/complexity of
structures used: subordinate clauses, passive voice, conditionals, modal
verbs, gerund/infinitive as subject, etc. The method gives a direction, not
a precise score - this is explicitly stated in the final result's
limitations.
"""

from __future__ import annotations

from dataclasses import dataclass

from apps.writing.services.nlp import get_nlp

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

_CONDITIONAL_MARKERS = {"if", "unless", "provided", "providing"}
_MODAL_LEMMAS = {"can", "could", "may", "might", "must", "shall", "should", "will", "would"}
_SUBORDINATORS = {
    "because", "although", "though", "while", "since", "unless", "whereas",
    "if", "when", "before", "after", "until", "as",
}


@dataclass(frozen=True)
class GrammarComplexityAnalysis:
    complexity_level: str | None
    avg_sentence_length: float
    subordinate_clause_ratio: float
    passive_voice_count: int
    conditional_count: int
    distinct_modal_count: int


def analyze_grammar_complexity(text: str) -> GrammarComplexityAnalysis:
    if not text or not text.strip():
        return GrammarComplexityAnalysis(
            complexity_level=None,
            avg_sentence_length=0.0,
            subordinate_clause_ratio=0.0,
            passive_voice_count=0,
            conditional_count=0,
            distinct_modal_count=0,
        )

    nlp = get_nlp()
    doc = nlp(text)
    sentences = list(doc.sents)
    if not sentences:
        return GrammarComplexityAnalysis(
            complexity_level=None,
            avg_sentence_length=0.0,
            subordinate_clause_ratio=0.0,
            passive_voice_count=0,
            conditional_count=0,
            distinct_modal_count=0,
        )

    word_tokens = [t for t in doc if t.is_alpha]
    avg_sentence_length = len(word_tokens) / len(sentences)

    subordinate_sentences = 0
    passive_voice_count = 0
    conditional_count = 0
    modal_lemmas_used: set[str] = set()

    for sent in sentences:
        has_subordinator = any(
            tok.dep_ in {"mark", "advcl"} and tok.lemma_.lower() in _SUBORDINATORS
            for tok in sent
        )
        if has_subordinator:
            subordinate_sentences += 1

        if any(tok.lemma_.lower() in _CONDITIONAL_MARKERS and tok.dep_ == "mark" for tok in sent):
            conditional_count += 1

        for tok in sent:
            if tok.dep_ == "nsubjpass" or tok.dep_ == "auxpass":
                passive_voice_count += 1
                break

        for tok in sent:
            if tok.pos_ in {"AUX", "VERB"} and tok.lemma_.lower() in _MODAL_LEMMAS:
                modal_lemmas_used.add(tok.lemma_.lower())

    subordinate_clause_ratio = subordinate_sentences / len(sentences)

    # Heuristic scale: the longer the sentences, the more frequent the
    # subordinate clauses, passive voice, conditionals, and varied modal
    # verbs, the higher the assumed complexity.
    complexity_score = 0.0
    complexity_score += min(avg_sentence_length / 20.0, 1.0) * 2.0  # up to 2 points
    complexity_score += min(subordinate_clause_ratio, 1.0) * 2.0  # up to 2 points
    complexity_score += min(passive_voice_count / max(len(sentences), 1), 1.0) * 1.0  # up to 1 point
    complexity_score += (1.0 if conditional_count > 0 else 0.0)  # up to 1 point
    complexity_score += min(len(modal_lemmas_used) / 4.0, 1.0) * 1.0  # up to 1 point

    # complexity_score is in [0, 7] -> map to a CEFR level.
    normalized = 1 + (complexity_score / 7.0) * (len(CEFR_ORDER) - 1)
    level_index = max(0, min(len(CEFR_ORDER) - 1, round(normalized) - 1))
    complexity_level = CEFR_ORDER[level_index]

    return GrammarComplexityAnalysis(
        complexity_level=complexity_level,
        avg_sentence_length=round(avg_sentence_length, 2),
        subordinate_clause_ratio=round(subordinate_clause_ratio, 2),
        passive_voice_count=passive_voice_count,
        conditional_count=conditional_count,
        distinct_modal_count=len(modal_lemmas_used),
    )
