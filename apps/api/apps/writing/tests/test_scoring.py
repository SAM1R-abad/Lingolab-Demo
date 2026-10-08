"""
scoring.py has no Django/ORM/external library dependency, so these are
plain unittest tests - no DB needed, and no LanguageTool/spaCy/cefrpy
installation required to run them.
"""

from __future__ import annotations

import unittest

from apps.writing.services import scoring


class GrammarAccuracyLevelTests(unittest.TestCase):
    def test_no_words_returns_none(self):
        self.assertIsNone(scoring.grammar_accuracy_level(grammar_error_count=0, word_count=0))

    def test_no_errors_is_top_level(self):
        self.assertEqual(scoring.grammar_accuracy_level(grammar_error_count=0, word_count=100), "C2")

    def test_dense_errors_is_low_level(self):
        # 30 errors per 100 words is well above the most lenient threshold (20/100).
        self.assertEqual(scoring.grammar_accuracy_level(grammar_error_count=30, word_count=100), "A1")

    def test_moderate_errors_is_mid_level(self):
        # 6 errors per 100 words should land in the B1/B2 range.
        level = scoring.grammar_accuracy_level(grammar_error_count=6, word_count=100)
        self.assertIn(level, {"B1", "B2"})


class OverallAssessmentTests(unittest.TestCase):
    def test_no_signals_returns_low_confidence_a1(self):
        result = scoring.compute_overall_assessment(
            lexical_complexity_level=None,
            grammar_accuracy_level=None,
            grammar_complexity_level=None,
            word_count=0,
            target_level=None,
        )
        self.assertEqual(result.cefr_level, "A1")
        self.assertEqual(result.confidence, "low")
        self.assertEqual(result.score, 0)

    def test_all_c2_signals_yield_c2_high_confidence(self):
        result = scoring.compute_overall_assessment(
            lexical_complexity_level="C2",
            grammar_accuracy_level="C2",
            grammar_complexity_level="C2",
            word_count=200,
            target_level=None,
        )
        self.assertEqual(result.cefr_level, "C2")
        self.assertEqual(result.score, 100)
        self.assertEqual(result.confidence, "high")

    def test_single_c1_word_does_not_dominate_overall_level(self):
        # Key product requirement: a single C1 word must not "pull" the
        # whole text to C1 if the other signals are A2/B1.
        result = scoring.compute_overall_assessment(
            lexical_complexity_level="A2",  # averaged vocabulary, not one word
            grammar_accuracy_level="B1",
            grammar_complexity_level="A2",
            word_count=120,
            target_level=None,
        )
        self.assertNotIn(result.cefr_level, {"C1", "C2"})

    def test_short_text_lowers_confidence(self):
        result = scoring.compute_overall_assessment(
            lexical_complexity_level="B2",
            grammar_accuracy_level="B2",
            grammar_complexity_level="B2",
            word_count=15,
            target_level=None,
        )
        self.assertEqual(result.confidence, "low")

    def test_missing_one_signal_caps_confidence_at_medium(self):
        result = scoring.compute_overall_assessment(
            lexical_complexity_level="B1",
            grammar_accuracy_level="B1",
            grammar_complexity_level=None,
            word_count=150,
            target_level=None,
        )
        self.assertEqual(result.confidence, "medium")

    def test_target_level_mentioned_in_rationale_when_below(self):
        result = scoring.compute_overall_assessment(
            lexical_complexity_level="A2",
            grammar_accuracy_level="A2",
            grammar_complexity_level="A2",
            word_count=100,
            target_level="B2",
        )
        self.assertIn("B2", result.rationale)


class StrengthsWeaknessesTests(unittest.TestCase):
    def test_high_spelling_error_ratio_is_flagged(self):
        strengths, weaknesses = scoring.build_strengths_and_weaknesses(
            vocabulary_distribution={"A1": 10},
            lexical_complexity_level="A1",
            grammar_accuracy_level="A2",
            grammar_complexity_level="A1",
            spelling_error_count=10,
            grammar_error_count=0,
            word_count=100,
        )
        self.assertTrue(any("spelling" in w.lower() for w in weaknesses))

    def test_advanced_vocabulary_is_flagged_as_strength(self):
        strengths, _ = scoring.build_strengths_and_weaknesses(
            vocabulary_distribution={"A1": 20, "B2": 4, "C1": 2},
            lexical_complexity_level="B1",
            grammar_accuracy_level="B1",
            grammar_complexity_level="B1",
            spelling_error_count=0,
            grammar_error_count=0,
            word_count=100,
        )
        self.assertTrue(any("B2" in s for s in strengths))

    def test_always_returns_at_least_one_item_each(self):
        strengths, weaknesses = scoring.build_strengths_and_weaknesses(
            vocabulary_distribution={},
            lexical_complexity_level=None,
            grammar_accuracy_level=None,
            grammar_complexity_level=None,
            spelling_error_count=0,
            grammar_error_count=0,
            word_count=0,
        )
        self.assertGreaterEqual(len(strengths), 1)
        self.assertGreaterEqual(len(weaknesses), 1)


if __name__ == "__main__":
    unittest.main()
