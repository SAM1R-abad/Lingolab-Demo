from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from apps.writing.models import SubmissionStatus, WritingResult, WritingSubmission
from apps.writing.services.language_check import LanguageCheckError
from apps.writing.services.persistence import persist_analysis_result
from apps.writing.services.pipeline import analyze_writing

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(LanguageCheckError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def analyze_writing_submission(self, submission_id: int) -> None:
    """
    Asynchronous analysis of a single submission. Idempotent with respect to
    status: re-running it for an already-completed submission is safe but
    recomputes the result from scratch (used e.g. for a manual re-run).
    """
    try:
        submission = WritingSubmission.objects.select_related("task").get(pk=submission_id)
    except WritingSubmission.DoesNotExist:
        logger.warning("WritingSubmission %s not found, skipping", submission_id)
        return

    submission.status = SubmissionStatus.PROCESSING
    submission.error_message = ""
    submission.save(update_fields=["status", "error_message"])

    try:
        analysis = analyze_writing(
            submitted_text=submission.submitted_text,
            target_level=submission.task.target_level,
            expected_vocabulary=submission.task.expected_vocabulary,
        )
        # Delete any result from a previous analysis attempt so re-runs
        # don't create duplicates.
        WritingResult.objects.filter(submission=submission).delete()
        submission.spelling_errors.all().delete()
        submission.grammar_errors.all().delete()

        persist_analysis_result(submission, analysis)

        submission.status = SubmissionStatus.COMPLETED
        submission.completed_at = timezone.now()
        submission.save(update_fields=["status", "completed_at"])
    except Exception as exc:  # noqa: BLE001 - any analysis failure must land in the submission's status
        logger.exception("Writing analysis failed for submission %s", submission_id)
        submission.status = SubmissionStatus.FAILED
        submission.error_message = str(exc)
        submission.save(update_fields=["status", "error_message"])
        raise
