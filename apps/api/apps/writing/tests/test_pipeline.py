"""
Tests for pipeline.analyze_writing with the "heavy" dependencies (the
LanguageTool server, spaCy, cefrpy) mocked out - these are unit tests of the
result-combination logic, not of the NLP tools themselves.
"""

from __future__ import annotations

import unittest
from unittest import mock

from apps.writing.services.grammar_complexity import GrammarComplexityAnalysis
from apps.writing.services.language_check import GrammarIssue, LanguageCheckResult, SpellingIssue
from apps.writing.services.relevance import RelevanceAnalysis
from apps.writing.services.vocabulary import VocabularyAnalysis


_UNSET = object()  # sentinel: distinguishes "not passed" from an explicit None


class AnalyzeWritingTests(unittest.TestCase):
    def _patch_all(
        self,
        *,
        word_count=100,
        sentence_count=8,
        spelling_issues=None,
        grammar_issues=None,
        vocabulary_distribution=None,
        lexical_complexity_level="B1",
        grammar_complexity_level="A2",
        relevance_result=_UNSET,
    ):
        spelling_issues = spelling_issues or []
        grammar_issues = grammar_issues or []
        vocabulary_distribution = vocabulary_distribution or {
            "A1": 25, "A2": 35, "B1": 30, "B2": 5, "C1": 0, "C2": 0, "unknown": 5,
        }
        if relevance_result is _UNSET:
            relevance_result = RelevanceAnalysis(
                relevance="relevant",
                matched_core_count=6,
                total_core_count=10,
                matched_keywords=["house", "tree"],
            )

        patches = [
            mock.patch(
                "apps.writing.services.pipeline._count_words_and_sentences",
                return_value=(word_count, sentence_count),
            ),
            mock.patch(
                "apps.writing.services.pipeline.check_text",
                return_value=LanguageCheckResult(
                    spelling_issues=spelling_issues, grammar_issues=grammar_issues
                ),
            ),
            mock.patch(
                "apps.writing.services.pipeline.analyze_vocabulary",
                return_value=VocabularyAnalysis(
                    distribution=vocabulary_distribution,
                    dominant_level=max(
                        ("A1", "A2", "B1", "B2", "C1", "C2"),
                        key=lambda lvl: vocabulary_distribution.get(lvl, 0),
                    ),
                    lexical_complexity_level=lexical_complexity_level,
                    analyzed_word_count=word_count,
                ),
            ),
            mock.patch(
                "apps.writing.services.pipeline.analyze_grammar_complexity",
                return_value=GrammarComplexityAnalysis(
                    complexity_level=grammar_complexity_level,
                    avg_sentence_length=12.0,
                    subordinate_clause_ratio=0.1,
                    passive_voice_count=0,
                    conditional_count=0,
                    distinct_modal_count=1,
                ),
            ),
            mock.patch(
                "apps.writing.services.pipeline.relevance.analyze_relevance",
                return_value=relevance_result,
            ),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_returns_structured_result_with_all_fields(self):
        from apps.writing.services.pipeline import analyze_writing

        self._patch_all()
        result = analyze_writing(
            submitted_text="Some text here.", target_level="B1", expected_vocabulary=[{"name": "house"}]
        )

        self.assertEqual(result.word_count, 100)
        self.assertEqual(result.sentence_count, 8)
        self.assertIn(result.overall_cefr_level, {"A1", "A2", "B1", "B2", "C1", "C2"})
        self.assertTrue(result.limitations)  # method limitations must always be present
        self.assertTrue(result.feedback)
        self.assertEqual(result.topic_relevance, "relevant")
        self.assertEqual(result.topic_relevance_details["matched_core_count"], 6)
        # dominant level (mode of the distribution) must be reported and
        # kept independent of lexical_complexity_level (weighted average).
        self.assertEqual(result.dominant_vocabulary_level, "A2")  # mode of {A1:25, A2:35, B1:30, ...}
        self.assertNotEqual(result.dominant_vocabulary_level, result.lexical_complexity_level)

    def test_spelling_and_grammar_stay_separated(self):
        spelling = [SpellingIssue(word="teh", suggestion="the", error_type="TYPO", start_offset=0, end_offset=3)]
        grammar = [
            GrammarIssue(
                fragment="he go",
                suggestion="he goes",
                short_description="Subject-verb agreement",
                rule_id="SVA",
                category="GRAMMAR",
                start_offset=10,
                end_offset=15,
            )
        ]
        self._patch_all(spelling_issues=spelling, grammar_issues=grammar)

        from apps.writing.services.pipeline import analyze_writing

        result = analyze_writing(submitted_text="he go teh school", target_level=None)

        self.assertEqual(len(result.spelling_issues), 1)
        self.assertEqual(len(result.grammar_issues), 1)
        self.assertEqual(result.spelling_issues[0].word, "teh")
        self.assertEqual(result.grammar_issues[0].fragment, "he go")

    def test_high_error_density_lowers_grammar_accuracy_level(self):
        from apps.writing.services.pipeline import analyze_writing

        many_grammar_errors = [
            GrammarIssue(
                fragment="x", suggestion="y", short_description="", rule_id="R",
                category="GRAMMAR", start_offset=i, end_offset=i + 1,
            )
            for i in range(25)
        ]
        self._patch_all(word_count=100, grammar_issues=many_grammar_errors)

        result = analyze_writing(submitted_text="text", target_level=None)
        self.assertEqual(result.grammar_accuracy_level, "A1")

    def test_no_expected_vocabulary_means_no_relevance_reported(self):
        from apps.writing.services.pipeline import analyze_writing

        self._patch_all(relevance_result=None)

        result = analyze_writing(submitted_text="text", target_level=None, expected_vocabulary=[])
        self.assertIsNone(result.topic_relevance)
        self.assertEqual(result.topic_relevance_details, {})


if __name__ == "__main__":
    unittest.main()
