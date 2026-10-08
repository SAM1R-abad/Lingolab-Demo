"""
Adaptive placement-test engine.

This module is the highest-priority piece of the Sprint 1 backend: it
decides which questions to serve next and how to interpret a user's
performance, exactly the "algorithm that automatically adjusts exercise
difficulty based on learner performance" described in the project brief.

Algorithm (per-skill adaptive placement test):
    1. Start at CEFR level A1.
    2. Serve a batch of `ASSESSMENT_BATCH_SIZE` random, unused questions
       at the current level.
    3. Once every question in the batch has been answered, score the
       batch (correct / total * 100).
    4. If the score >= `ASSESSMENT_PASS_THRESHOLD_PERCENT`:
         - mark the level as passed;
         - if it was the last level (C2), the session is complete with
           result_level = C2;
         - otherwise, advance to the next level and serve a new batch.
       If the score is below the threshold:
         - the session is complete;
         - result_level = the highest previously-passed level, or
           "Pre-A1" if no level was passed (including A1 itself).

This mirrors the scoring methodology recommended in
`cefr_test_json_documentation.md`, applied incrementally so that a
learner does not have to answer all 6 levels' worth of questions before
the platform can determine their level.
"""

import random

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import CEFRLevel, PlacementSession, Question, SessionQuestion


class AdaptiveEngineError(Exception):
    """Raised for invalid engine operations (e.g. answering a finished session)."""


LEVEL_ORDER = CEFRLevel.order()


def _next_level(level):
    idx = LEVEL_ORDER.index(level)
    if idx + 1 >= len(LEVEL_ORDER):
        return None
    return LEVEL_ORDER[idx + 1]


class AdaptiveEngine:
    """Stateless service operating on a given PlacementSession."""

    def __init__(self, session: PlacementSession):
        self.session = session

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def start(cls, user, skill: str) -> PlacementSession:
        session = PlacementSession.objects.create(
            user=user,
            skill=skill,
            current_level=CEFRLevel.A1,
        )
        cls(session)._serve_batch(CEFRLevel.A1)
        return session

    def _serve_batch(self, level):
        batch_size = settings.ASSESSMENT_BATCH_SIZE
        already_used_ids = SessionQuestion.objects.filter(session=self.session).values_list(
            "question_id", flat=True
        )
        pool = list(
            Question.objects.filter(skill=self.session.skill, level=level).exclude(
                id__in=already_used_ids
            )
        )
        if not pool:
            raise AdaptiveEngineError(
                f"No questions available for skill={self.session.skill} level={level}."
            )
        sample_size = min(batch_size, len(pool))
        chosen = random.sample(pool, sample_size)

        for order, question in enumerate(chosen, start=1):
            SessionQuestion.objects.create(
                session=self.session,
                question=question,
                level=level,
                order=order,
            )

    # ------------------------------------------------------------------
    # Answering
    # ------------------------------------------------------------------
    def current_batch(self):
        """Unanswered (and answered) questions for the current level batch."""
        return (
            SessionQuestion.objects.filter(session=self.session, level=self.session.current_level)
            .select_related("question")
            .order_by("order")
        )

    @transaction.atomic
    def submit_answer(self, question_id: int, answer: str) -> SessionQuestion:
        if self.session.status == PlacementSession.Status.COMPLETED:
            raise AdaptiveEngineError("This placement session is already completed.")

        try:
            session_question = SessionQuestion.objects.select_related("question").get(
                session=self.session,
                question_id=question_id,
                level=self.session.current_level,
            )
        except SessionQuestion.DoesNotExist:
            raise AdaptiveEngineError(
                "This question does not belong to the current batch of this session."
            )

        if session_question.answered_at is not None:
            raise AdaptiveEngineError("This question was already answered.")

        session_question.selected_answer = answer
        session_question.is_correct = answer.strip() == session_question.question.correct_answer.strip()
        session_question.answered_at = timezone.now()
        session_question.save()

        if self._is_batch_complete():
            self._evaluate_level()

        return session_question

    def _is_batch_complete(self) -> bool:
        return not self.current_batch().filter(answered_at__isnull=True).exists()

    # ------------------------------------------------------------------
    # Adaptive decision
    # ------------------------------------------------------------------
    def _evaluate_level(self):
        batch = self.current_batch()
        total = batch.count()
        correct = batch.filter(is_correct=True).count()
        score_percent = (correct / total) * 100 if total else 0
        threshold = settings.ASSESSMENT_PASS_THRESHOLD_PERCENT

        level = self.session.current_level

        if score_percent >= threshold:
            passed_levels = self.session.passed_levels + [level]
            self.session.passed_levels = passed_levels

            next_level = _next_level(level)
            if next_level is None:
                # Passed C2 - top of the scale, nothing more to test.
                self._complete_session(result_level=level)
                return

            self.session.current_level = next_level
            self.session.save()
            self._serve_batch(next_level)
        else:
            result_level = self.session.passed_levels[-1] if self.session.passed_levels else "Pre-A1"
            self._complete_session(result_level=result_level)

    def _complete_session(self, result_level: str):
        self.session.status = PlacementSession.Status.COMPLETED
        self.session.result_level = result_level
        self.session.completed_at = timezone.now()
        self.session.save()

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def level_breakdown(self):
        """Per-level score breakdown for this session so far, for diagnostics."""
        breakdown = []
        qs = SessionQuestion.objects.filter(session=self.session, answered_at__isnull=False)
        for level in LEVEL_ORDER:
            level_qs = qs.filter(level=level)
            total = level_qs.count()
            if total == 0:
                continue
            correct = level_qs.filter(is_correct=True).count()
            breakdown.append(
                {
                    "level": level,
                    "total_questions": total,
                    "correct_answers": correct,
                    "score_percent": round((correct / total) * 100, 1),
                    "passed": level in self.session.passed_levels,
                }
            )
        return breakdown
