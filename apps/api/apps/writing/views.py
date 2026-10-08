from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin
from apps.common.pagination import StandardResultsSetPagination
from apps.writing.models import SubmissionStatus, WritingSubmission, WritingTask
from apps.writing.serializers import (
    WritingSubmissionCreateSerializer,
    WritingSubmissionDetailSerializer,
    WritingSubmissionListSerializer,
    WritingTaskAdminSerializer,
    WritingTaskSerializer,
)
from apps.writing.tasks import analyze_writing_submission

logger = logging.getLogger(__name__)


def _submission_for_user(submission_id, user):
    return get_object_or_404(
        WritingSubmission.objects.select_related("task", "result"), pk=submission_id, user=user
    )


@extend_schema(summary="List active Writing tasks available to students")
class WritingTaskListView(generics.ListAPIView):
    """GET /api/v1/writing/tasks/"""

    serializer_class = WritingTaskSerializer

    def get_queryset(self):
        return WritingTask.objects.filter(is_active=True)


@extend_schema(summary="Get a single Writing task (instructions + SVG material)")
class WritingTaskDetailView(generics.RetrieveAPIView):
    """GET /api/v1/writing/tasks/{id}/"""

    serializer_class = WritingTaskSerializer
    queryset = WritingTask.objects.filter(is_active=True)


@extend_schema(
    summary="List submissions (GET) / submit a Writing response for analysis (POST)",
    description=(
        "GET returns the current user's submission history (used by the "
        "Progress screen). POST creates a new writing submission for the "
        "given `task_id` and schedules asynchronous analysis (spelling, "
        "grammar, vocabulary/CEFR distribution, topic relevance, overall "
        "score). Poll `GET /api/v1/writing/submissions/{id}/` until "
        "`status` becomes `completed` (or `failed`)."
    ),
    request=WritingSubmissionCreateSerializer,
)
class WritingSubmissionListCreateView(APIView):
    """GET/POST /api/v1/writing/submissions/"""

    def get(self, request, *args, **kwargs):
        submissions = (
            WritingSubmission.objects.filter(user=request.user)
            .select_related("task", "result")
        )
        return Response(WritingSubmissionListSerializer(submissions, many=True).data)

    def post(self, request, *args, **kwargs):
        serializer = WritingSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = WritingSubmission.objects.create(
            user=request.user,
            task=serializer.validated_data["task"],
            submitted_text=serializer.validated_data["submitted_text"],
        )

        # In normal (async) operation .delay() only enqueues and returns
        # instantly - it cannot raise from task-body failures. In
        # WRITING_EAGER_MODE (dev convenience, no Celery worker/Redis
        # needed - see apps/writing/README.md), .delay() instead runs the
        # whole analysis synchronously right here, and
        # CELERY_TASK_EAGER_PROPAGATES re-raises any task failure (e.g.
        # LanguageTool being unreachable) at this call site. The task
        # itself already persists status=FAILED + error_message before
        # re-raising (see tasks.py), so the submission row is already in a
        # correct, pollable terminal state - we must not let this crash
        # the "submission created" response over it.
        try:
            analyze_writing_submission.delay(submission.id)
        except Exception:  # noqa: BLE001 - see comment above; only reachable in eager mode
            logger.exception(
                "analyze_writing_submission raised synchronously for submission %s "
                "(expected only under WRITING_EAGER_MODE=1)",
                submission.id,
            )

        return Response(
            WritingSubmissionDetailSerializer(submission, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(summary="Get a writing submission's status and result (if ready)")
class WritingSubmissionDetailView(APIView):
    """GET /api/v1/writing/submissions/{id}/"""

    def get(self, request, submission_id, *args, **kwargs):
        submission = _submission_for_user(submission_id, request.user)
        return Response(
            WritingSubmissionDetailSerializer(submission, context={"request": request}).data
        )


@extend_schema(summary="Get only the final result of a completed writing submission")
class WritingSubmissionResultView(APIView):
    """GET /api/v1/writing/submissions/{id}/result/"""

    def get(self, request, submission_id, *args, **kwargs):
        submission = _submission_for_user(submission_id, request.user)
        if submission.status != SubmissionStatus.COMPLETED:
            return Response(
                {
                    "detail": "Submission analysis is not completed yet.",
                    "status": submission.status,
                    "error_message": submission.error_message or None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = WritingSubmissionDetailSerializer(submission, context={"request": request}).data
        return Response(data["result"])


@extend_schema(
    summary="List / create Writing tasks (admin only)",
    description=(
        "Admin-only content management for Writing tasks, complementing "
        "`manage.py import_writing_tasks`. Regular users never see "
        "`expected_vocabulary` (the answer key) - they only get "
        "WritingTaskSerializer via /writing/tasks/."
    ),
)
class WritingTaskAdminListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/writing/admin/tasks/"""

    serializer_class = WritingTaskAdminSerializer
    permission_classes = (IsAdmin,)
    pagination_class = StandardResultsSetPagination
    queryset = WritingTask.objects.all()


@extend_schema(summary="Retrieve / update / delete a Writing task (admin only)")
class WritingTaskAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/v1/writing/admin/tasks/{id}/"""

    serializer_class = WritingTaskAdminSerializer
    permission_classes = (IsAdmin,)
    queryset = WritingTask.objects.all()
