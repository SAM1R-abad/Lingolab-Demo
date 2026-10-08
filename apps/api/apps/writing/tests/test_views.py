"""
Adapted from the standalone writing_assessment prototype's test_views.py.
Key differences here (matching the new models):
  - submissions require a `task_id` (no more free-text `task_prompt`);
  - task listing/detail endpoints are public-facing (auth still required,
    like everything else - see DEFAULT_PERMISSION_CLASSES);
  - admin task CRUD endpoints require IsAdmin and are covered separately.
"""

from __future__ import annotations

from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assessment.models import CEFRLevel
from apps.writing.models import SubmissionStatus, WritingResult, WritingSubmission, WritingTask

User = get_user_model()


def _make_task(**overrides):
    defaults = dict(
        key="01_house_and_garden",
        title="House and Garden",
        prompt="Describe the picture.",
        min_word_count=40,
        expected_vocabulary=[{"name": "house", "synonyms": [], "count": 1, "position": "", "attributes": [], "action": ""}],
    )
    defaults.update(overrides)
    return WritingTask.objects.create(**defaults)


class WritingTaskListViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student1", password="pass12345")
        self.client.force_authenticate(self.user)

    def test_lists_only_active_tasks(self):
        _make_task(key="01_house_and_garden")
        _make_task(key="02_city_street", title="City Street", is_active=False)

        response = self.client.get(reverse("writing:task-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["key"], "01_house_and_garden")

    def test_task_payload_does_not_leak_answer_key(self):
        _make_task()
        response = self.client.get(reverse("writing:task-list"))
        self.assertNotIn("expected_vocabulary", response.data[0])

    def test_task_payload_includes_absolute_svg_url(self):
        _make_task()
        response = self.client.get(reverse("writing:task-list"))
        svg_url = response.data[0]["svg_url"]
        # Absolute URL, under the writing/scenes/ static path, for the right
        # scene. Matched via regex (not a plain `.endswith(...)` check)
        # because WhiteNoise's ManifestStaticFilesStorage appends a content
        # hash to the filename (e.g. `01_house_and_garden.5b61368b4089.svg`)
        # once `collectstatic` has run, so the exact filename isn't stable.
        self.assertTrue(svg_url.startswith("http"))
        self.assertRegex(
            svg_url, r"/writing/scenes/01_house_and_garden(\.[0-9a-f]{12})?\.svg$"
        )

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse("writing:task-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WritingSubmissionListCreateViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student1", password="pass12345")
        self.client.force_authenticate(self.user)
        self.task = _make_task()
        self.url = reverse("writing:submission-list-create")

    @mock.patch("apps.writing.views.analyze_writing_submission")
    def test_create_submission_schedules_task(self, mock_task):
        response = self.client.post(
            self.url,
            {"task_id": self.task.id, "submitted_text": "This is my weekend story about a house."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], SubmissionStatus.PENDING)
        submission_id = response.data["id"]
        mock_task.delay.assert_called_once_with(submission_id)

    def test_create_rejects_missing_task(self):
        response = self.client.post(self.url, {"submitted_text": "Some valid text here."}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("task_id", response.data)

    def test_create_rejects_inactive_task(self):
        inactive = _make_task(key="99_inactive", is_active=False)
        response = self.client.post(
            self.url, {"task_id": inactive.id, "submitted_text": "Some valid text here."}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_empty_text(self):
        response = self.client.post(self.url, {"task_id": self.task.id, "submitted_text": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("submitted_text", response.data)

    def test_create_rejects_too_short_text(self):
        response = self.client.post(self.url, {"task_id": self.task.id, "submitted_text": "Hi"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_returns_own_submissions(self):
        other_user = User.objects.create_user(username="student2", password="pass12345")
        WritingSubmission.objects.create(user=other_user, task=self.task, submitted_text="Not mine.")
        WritingSubmission.objects.create(user=self.user, task=self.task, submitted_text="Mine.")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WritingSubmissionDetailViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student1", password="pass12345")
        self.client.force_authenticate(self.user)
        self.task = _make_task()

    def test_cannot_access_other_users_submission(self):
        other_user = User.objects.create_user(username="student2", password="pass12345")
        submission = WritingSubmission.objects.create(user=other_user, task=self.task, submitted_text="Not mine.")

        url = reverse("writing:submission-detail", args=[submission.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pending_submission_has_no_result(self):
        submission = WritingSubmission.objects.create(user=self.user, task=self.task, submitted_text="Some text.")
        url = reverse("writing:submission-detail", args=[submission.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["result"])
        self.assertEqual(response.data["task"]["key"], self.task.key)


class WritingSubmissionResultViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student1", password="pass12345")
        self.client.force_authenticate(self.user)
        self.task = _make_task()

    def test_returns_400_if_not_completed(self):
        submission = WritingSubmission.objects.create(user=self.user, task=self.task, submitted_text="Some text.")
        url = reverse("writing:submission-result", args=[submission.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_result_if_completed(self):
        submission = WritingSubmission.objects.create(
            user=self.user, task=self.task, submitted_text="Some text.", status=SubmissionStatus.COMPLETED
        )
        WritingResult.objects.create(
            submission=submission,
            overall_score=70,
            overall_cefr_level=CEFRLevel.B2,
            vocabulary_distribution={"A1": 10},
            dominant_vocabulary_level=CEFRLevel.A1,
        )
        url = reverse("writing:submission-result", args=[submission.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["overall_cefr_level"], "B2")
        self.assertEqual(response.data["dominant_vocabulary_level"], "A1")


class WritingTaskAdminViewTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin1", password="pass12345", role="admin")
        self.student = User.objects.create_user(username="student1", password="pass12345")

    def test_student_cannot_list_admin_tasks(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("writing:admin-task-list-create"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_task_with_answer_key(self):
        self.client.force_authenticate(self.admin)
        payload = {
            "key": "16_custom_scene",
            "title": "Custom Scene",
            "prompt": "Describe the picture.",
            "min_word_count": 40,
            "expected_vocabulary": [
                {"name": "cat", "synonyms": [], "count": 1, "position": "", "attributes": [], "action": ""}
            ],
        }
        response = self.client.post(reverse("writing:admin-task-list-create"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(WritingTask.objects.filter(key="16_custom_scene").exists())
