from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.writing.models import (
    GrammarError,
    SpellingError,
    SubmissionStatus,
    WritingResult,
    WritingSubmission,
    WritingTask,
)

User = get_user_model()


def _make_task(**overrides):
    defaults = dict(
        key="01_house_and_garden",
        title="House and Garden",
        prompt="Describe the picture.",
        min_word_count=40,
        expected_vocabulary=[
            {"name": "house", "synonyms": ["home"], "count": 1, "position": "", "attributes": [], "action": ""},
        ],
    )
    defaults.update(overrides)
    return WritingTask.objects.create(**defaults)


class WritingTaskModelTests(TestCase):
    def test_key_must_be_unique(self):
        _make_task()
        with self.assertRaises(Exception):
            _make_task()

    def test_svg_static_path_uses_key(self):
        task = _make_task(key="05_park")
        self.assertEqual(task.svg_static_path, "writing/scenes/05_park.svg")


class WritingSubmissionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student1", password="pass12345")
        self.task = _make_task()

    def test_default_status_is_pending(self):
        submission = WritingSubmission.objects.create(
            user=self.user, task=self.task, submitted_text="My weekend was great."
        )
        self.assertEqual(submission.status, SubmissionStatus.PENDING)
        self.assertIsNone(submission.completed_at)

    def test_ordering_is_newest_first(self):
        first = WritingSubmission.objects.create(user=self.user, task=self.task, submitted_text="First text.")
        second = WritingSubmission.objects.create(user=self.user, task=self.task, submitted_text="Second text.")
        submissions = list(WritingSubmission.objects.filter(user=self.user))
        self.assertEqual(submissions[0].pk, second.pk)
        self.assertEqual(submissions[1].pk, first.pk)

    def test_task_protected_from_deletion_while_referenced(self):
        WritingSubmission.objects.create(user=self.user, task=self.task, submitted_text="Some text.")
        with self.assertRaises(Exception):
            self.task.delete()


class WritingResultModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student2", password="pass12345")
        self.task = _make_task(key="02_city_street", title="City Street")
        self.submission = WritingSubmission.objects.create(
            user=self.user, task=self.task, submitted_text="Some text.", status=SubmissionStatus.COMPLETED
        )

    def test_one_to_one_with_submission(self):
        result = WritingResult.objects.create(
            submission=self.submission,
            overall_score=55,
            overall_cefr_level="B1",
            vocabulary_distribution={"A1": 10, "B1": 5, "unknown": 1},
            topic_relevance="relevant",
            topic_relevance_details={"matched_core_count": 5, "total_core_count": 10},
        )
        self.assertEqual(self.submission.result, result)
        self.assertEqual(result.topic_relevance, "relevant")

    def test_related_errors_are_ordered_by_offset(self):
        SpellingError.objects.create(
            submission=self.submission, word="teh", suggestion="the", start_offset=20, end_offset=23
        )
        SpellingError.objects.create(
            submission=self.submission, word="beleive", suggestion="believe", start_offset=0, end_offset=7
        )
        offsets = list(self.submission.spelling_errors.values_list("start_offset", flat=True))
        self.assertEqual(offsets, [0, 20])

    def test_grammar_error_cascade_delete_with_submission(self):
        GrammarError.objects.create(
            submission=self.submission,
            fragment="he go",
            suggestion="he goes",
            start_offset=0,
            end_offset=5,
        )
        submission_id = self.submission.pk
        self.submission.delete()
        self.assertEqual(GrammarError.objects.filter(submission_id=submission_id).count(), 0)
