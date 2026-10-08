from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin
from apps.common.pagination import StandardResultsSetPagination

from .models import CEFRLevel, PlacementSession, Question
from .serializers import (
    PlacementSessionSerializer,
    QuestionAdminSerializer,
    SessionQuestionSerializer,
    SessionResultSerializer,
    StartSessionSerializer,
    SubmitAnswerSerializer,
)
from .services import AdaptiveEngine, AdaptiveEngineError


def _session_for_user(session_id, user):
    return get_object_or_404(PlacementSession, pk=session_id, user=user)


@extend_schema(
    summary="Start an adaptive placement test",
    description=(
        "Creates a new placement-test session for the given skill "
        "(vocabulary or grammar) and returns the first batch of "
        "questions, starting at CEFR level A1."
    ),
    request=StartSessionSerializer,
)
class StartSessionView(APIView):
    """POST /api/v1/assessment/start/"""

    def post(self, request, *args, **kwargs):
        serializer = StartSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        skill = serializer.validated_data["skill"]

        try:
            session = AdaptiveEngine.start(user=request.user, skill=skill)
        except AdaptiveEngineError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        engine = AdaptiveEngine(session)
        batch = SessionQuestionSerializer(engine.current_batch(), many=True).data
        return Response(
            {
                "session": PlacementSessionSerializer(session).data,
                "questions": batch,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    summary="Submit an answer for the current batch",
    description=(
        "Submits the test-taker's chosen answer for one question in the "
        "current level batch. When the whole batch has been answered, "
        "the adaptive engine automatically scores the level and either "
        "advances to the next CEFR level (new batch returned) or "
        "completes the session (see `session.status` / `session.result_level`)."
    ),
    request=SubmitAnswerSerializer,
)
class SubmitAnswerView(APIView):
    """POST /api/v1/assessment/{session_id}/answer/"""

    def post(self, request, session_id, *args, **kwargs):
        session = _session_for_user(session_id, request.user)
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        engine = AdaptiveEngine(session)
        try:
            engine.submit_answer(
                question_id=serializer.validated_data["question_id"],
                answer=serializer.validated_data["answer"],
            )
        except AdaptiveEngineError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        session.refresh_from_db()

        response = {"session": PlacementSessionSerializer(session).data}
        if session.status == PlacementSession.Status.IN_PROGRESS:
            response["questions"] = SessionQuestionSerializer(
                engine.current_batch(), many=True
            ).data
        else:
            response["result"] = SessionResultSerializer(
                session, context={"level_breakdown": engine.level_breakdown()}
            ).data
        return Response(response, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get placement session status and current batch",
    description="Returns 404 if the session doesn't exist or doesn't belong to the caller.",
)
class SessionStatusView(APIView):
    """GET /api/v1/assessment/{session_id}/"""

    def get(self, request, session_id, *args, **kwargs):
        session = _session_for_user(session_id, request.user)
        engine = AdaptiveEngine(session)
        return Response(
            {
                "session": PlacementSessionSerializer(session).data,
                "questions": SessionQuestionSerializer(engine.current_batch(), many=True).data,
            }
        )


@extend_schema(
    summary="Get the final result of a completed placement session",
    description=(
        "Returns 404 if the session doesn't exist or doesn't belong to the "
        "caller, 400 if the session is still in progress (not completed yet)."
    ),
)
class SessionResultView(APIView):
    """GET /api/v1/assessment/{session_id}/result/"""

    def get(self, request, session_id, *args, **kwargs):
        session = _session_for_user(session_id, request.user)
        if session.status != PlacementSession.Status.COMPLETED:
            return Response(
                {"detail": "Session is still in progress."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        engine = AdaptiveEngine(session)
        data = SessionResultSerializer(
            session, context={"level_breakdown": engine.level_breakdown()}
        ).data
        return Response(data)


@extend_schema(summary="List the current user's placement-test sessions (history)")
class SessionListView(APIView):
    """GET /api/v1/assessment/sessions/ - used by the Progress screen."""

    def get(self, request, *args, **kwargs):
        sessions = PlacementSession.objects.filter(user=request.user)
        return Response(PlacementSessionSerializer(sessions, many=True).data)


@extend_schema(summary="Static CEFR level reference (A1-C2 names)")
class CefrLevelsView(APIView):
    """GET /api/v1/assessment/levels/ - convenience lookup for UI labels."""

    def get(self, request, *args, **kwargs):
        return Response({level.value: level.label for level in CEFRLevel})


@extend_schema(
    summary="List / create questions (admin only)",
    description=(
        "Admin-only content management for the question bank, complementing "
        "`manage.py import_questions`. Supports optional `?skill=` and "
        "`?level=` filters on GET. Regular users never see this endpoint's "
        "data directly - test-takers only receive questions (without "
        "`correct_answer`) via the placement-test batch endpoints."
    ),
    parameters=[
        OpenApiParameter("skill", str, description="Filter by skill, e.g. vocabulary"),
        OpenApiParameter("level", str, description="Filter by CEFR level, e.g. B1"),
    ],
)
class QuestionListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/assessment/questions/"""

    serializer_class = QuestionAdminSerializer
    permission_classes = (IsAdmin,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = Question.objects.all()
        skill = self.request.query_params.get("skill")
        level = self.request.query_params.get("level")
        if skill:
            qs = qs.filter(skill=skill)
        if level:
            qs = qs.filter(level=level)
        return qs


@extend_schema(
    summary="Retrieve / update / delete a question (admin only)",
    description="Returns 403 for any non-admin caller, 404 if the question id doesn't exist.",
)
class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/v1/assessment/questions/{id}/"""

    queryset = Question.objects.all()
    serializer_class = QuestionAdminSerializer
    permission_classes = (IsAdmin,)
