"""
Tests for services/relevance.py - the topic/keyword-overlap analysis that
did not exist in the standalone writing_assessment prototype and was
written specifically for the answer_keys.json data (see the module
docstring for the method's deliberate limitations).

Uses the real spaCy pipeline (through get_nlp()) rather than mocking it,
since lemma matching is the core thing under test here. Requires
en_core_web_sm to be installed - same requirement as the rest of the
writing app's test suite.
"""

from __future__ import annotations

import unittest

from apps.writing.services.relevance import analyze_relevance

HOUSE_GARDEN_VOCAB = [
    {"name": "house", "synonyms": ["home"], "count": 1, "position": "center", "attributes": ["red roof"], "action": ""},
    {"name": "tree", "synonyms": [], "count": 2, "position": "left of the house", "attributes": ["tall"], "action": ""},
    {"name": "dog", "synonyms": ["puppy"], "count": 1, "position": "garden", "attributes": [], "action": "running"},
    {"name": "flower", "synonyms": ["flowers"], "count": 0, "position": "", "attributes": [], "action": ""},  # optional
]


class AnalyzeRelevanceTests(unittest.TestCase):
    def test_no_expected_vocabulary_returns_none(self):
        result = analyze_relevance(submitted_text="Anything at all.", expected_vocabulary=[])
        self.assertIsNone(result)

    def test_high_overlap_is_relevant(self):
        text = "There is a big house with a red roof. A tall tree stands next to the house, and a dog is running in the garden."
        result = analyze_relevance(submitted_text=text, expected_vocabulary=HOUSE_GARDEN_VOCAB)
        self.assertEqual(result.relevance, "relevant")
        self.assertEqual(result.total_core_count, 3)  # flower excluded, count == 0
        self.assertGreaterEqual(result.matched_core_count, 2)

    def test_synonym_counts_as_a_match(self):
        text = "My home is small but cozy."
        result = analyze_relevance(submitted_text=text, expected_vocabulary=HOUSE_GARDEN_VOCAB)
        self.assertIn("house", result.matched_keywords)

    def test_unrelated_text_is_weakly_relevant_not_penalized_as_error(self):
        text = "Yesterday I went to the cinema and watched a movie about space travel."
        result = analyze_relevance(submitted_text=text, expected_vocabulary=HOUSE_GARDEN_VOCAB)
        self.assertEqual(result.relevance, "weakly_relevant")
        # Never negative / error-like - just a low match count.
        self.assertEqual(result.matched_core_count, 0)

    def test_optional_object_missing_is_never_penalized(self):
        # "flower" has count == 0 (optional per the JSON's usage_notes) and
        # is absent from the text - this must not affect the classification
        # or appear anywhere as a deduction.
        text = "There is a house and a tree with a dog running around."
        result = analyze_relevance(submitted_text=text, expected_vocabulary=HOUSE_GARDEN_VOCAB)
        self.assertNotIn("flower", result.matched_keywords)
        self.assertIn(result.relevance, {"relevant", "partially_relevant"})

    def test_optional_object_mentioned_is_bonus_only(self):
        text = "There are some flowers in front of the house."
        result = analyze_relevance(submitted_text=text, expected_vocabulary=HOUSE_GARDEN_VOCAB)
        self.assertTrue(any("flower" in m for m in result.bonus_matches))

    def test_limitations_text_is_always_present(self):
        result = analyze_relevance(submitted_text="A house.", expected_vocabulary=HOUSE_GARDEN_VOCAB)
        self.assertTrue(result.limitations)
        self.assertIn("does not measure true semantic understanding", result.limitations)


if __name__ == "__main__":
    unittest.main()
