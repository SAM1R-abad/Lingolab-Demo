"""
Writing Assessment models.

Design notes (see the integration plan discussed with the team):

- `CEFRLevel` is imported from `apps.assessment.models` instead of being
  redefined here (the standalone writing_assessment prototype duplicated it
  intentionally, for isolated development - now that it's being merged into
  the main project, we use the single shared definition).
- `Skill.WRITING` already exists in `apps.assessment.models.Skill`, but
  WritingTask/WritingSubmission deliberately do NOT hook into
  `apps.assessment.PlacementSession` - that model is specific to the
  adaptive multiple-choice placement engine (CEFR batches, pass thresholds),
  which doesn't fit free-text writing submissions. Writing gets its own
  submission/result models and its own history, surfaced next to (not
  inside) placement-test history on the Progress screen.
- A submission is always tied to a `WritingTask` (picture-description task
  backed by an SVG + expected-vocabulary answer key) rather than a free-form
  `task_prompt` string, so that topic-relevance analysis has something to
  compare against.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.assessment.models import CEFRLevel


class SubmissionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class ConfidenceLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class TopicRelevance(models.TextChoices):
    """
    Coarse, keyword-overlap-based relevance classification (see
    services/relevance.py). Intentionally only 3 bands, per the product
    brief: this is a demo-level heuristic signal, not a semantic model.
    """

    RELEVANT = "relevant", "Relevant"
    PARTIALLY_RELEVANT = "partially_relevant", "Partially relevant"
    WEAKLY_RELEVANT = "weakly_relevant", "Weakly relevant"


class WritingTask(models.Model):
    """
    A single picture-description writing task: an instruction/prompt shown
    to the student, paired with an SVG scene and its "expected vocabulary"
    answer key (bulk-loaded from data/answer_keys.json + static/writing/scenes/
    via `manage.py import_writing_tasks` - mirrors
    apps.assessment.management.commands.import_questions).
    """

    key = models.SlugField(
        max_length=64,
        unique=True,
        help_text=(
            "Matches the scene id in answer_keys.json and the SVG filename "
            "stem in apps/writing/static/writing/scenes/ (e.g. "
            "'01_house_and_garden')."
        ),
    )
    title = models.CharField(max_length=255)
    prompt = models.TextField(
        help_text="Instructions shown to the student above the writing editor.",
    )
    target_level = models.CharField(
        max_length=2,
        choices=CEFRLevel.choices,
        null=True,
        blank=True,
        help_text="Suggested CEFR level for this task, if any.",
    )
    min_word_count = models.PositiveIntegerField(
        default=40,
        help_text="Soft minimum shown to the student as writing guidance.",
    )
    expected_vocabulary = models.JSONField(
        default=list,
        help_text=(
            "Copy of this scene's 'objects' list from answer_keys.json "
            "(name/synonyms/count/position/attributes/action per object). "
            "Used by services/relevance.py for topic-relevance analysis."
        ),
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "key"]

    def __str__(self) -> str:
        return f"WritingTask({self.key})"

    @property
    def svg_static_path(self) -> str:
        """Relative static path, resolved by the frontend via STATIC_URL."""
        return f"writing/scenes/{self.key}.svg"


class WritingSubmission(models.Model):
    """One attempt by a user to respond to a WritingTask."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="writing_submissions",
    )
    task = models.ForeignKey(
        WritingTask,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    submitted_text = models.TextField(help_text="Text written by the user.")
    status = models.CharField(
        max_length=12,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
    )
    error_message = models.TextField(
        blank=True,
        default="",
        help_text="Populated if analysis failed (status=failed).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"WritingSubmission #{self.pk} (user={self.user_id}, status={self.status})"


class WritingResult(models.Model):
    """
    Aggregated analysis result for one submission.

    Levels are kept deliberately separate: individual word CEFR level
    (vocabulary_distribution), lexical complexity (lexical_complexity_level),
    grammar accuracy (grammar_accuracy_level), grammar/syntax complexity
    (grammar_complexity_level), topic relevance (topic_relevance), and the
    final blended estimate (overall_cefr_level) all measure different
    things - a single advanced word must never by itself push the overall
    result up.
    """

    submission = models.OneToOneField(
        WritingSubmission, on_delete=models.CASCADE, related_name="result"
    )

    overall_score = models.PositiveSmallIntegerField(
        help_text="0-100 helper metric for the UI (progress bar etc.), not a standalone verdict."
    )
    overall_cefr_level = models.CharField(max_length=2, choices=CEFRLevel.choices)
    confidence = models.CharField(
        max_length=6, choices=ConfidenceLevel.choices, default=ConfidenceLevel.MEDIUM
    )
    rationale = models.TextField(blank=True, default="")

    word_count = models.PositiveIntegerField(default=0)
    sentence_count = models.PositiveIntegerField(default=0)

    vocabulary_distribution = models.JSONField(
        default=dict,
        help_text='e.g. {"A1": 25, "A2": 35, ..., "unknown": 5}.',
    )
    dominant_vocabulary_level = models.CharField(
        max_length=2,
        choices=CEFRLevel.choices,
        null=True,
        blank=True,
        help_text=(
            "The single most frequent CEFR level in vocabulary_distribution "
            "(excluding 'unknown'). Deliberately distinct from "
            "lexical_complexity_level (a weighted average) - see "
            "services/vocabulary.py."
        ),
    )
    lexical_complexity_level = models.CharField(
        max_length=2, choices=CEFRLevel.choices, null=True, blank=True
    )

    grammar_accuracy_level = models.CharField(
        max_length=2, choices=CEFRLevel.choices, null=True, blank=True
    )
    grammar_complexity_level = models.CharField(
        max_length=2, choices=CEFRLevel.choices, null=True, blank=True
    )

    topic_relevance = models.CharField(
        max_length=20, choices=TopicRelevance.choices, null=True, blank=True
    )
    topic_relevance_details = models.JSONField(
        default=dict,
        help_text=(
            "matched_objects/total_core_objects, matched keyword list, "
            "bonus position/attribute/action matches - see services/relevance.py."
        ),
    )

    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    feedback = models.TextField(blank=True, default="")
    limitations = models.TextField(
        blank=True,
        default="",
        help_text="Explicit description of the method's limitations - always populated.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"WritingResult(submission={self.submission_id}, level={self.overall_cefr_level})"


class SpellingError(models.Model):
    submission = models.ForeignKey(
        WritingSubmission, on_delete=models.CASCADE, related_name="spelling_errors"
    )
    word = models.CharField(max_length=255)
    suggestion = models.CharField(max_length=255, blank=True, default="")
    error_type = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Rule category from the analyzer (e.g. MORFOLOGIK_RULE_EN_US).",
    )
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()

    class Meta:
        ordering = ["start_offset"]

    def __str__(self) -> str:
        return f"SpellingError({self.word!r} -> {self.suggestion!r})"


class GrammarError(models.Model):
    submission = models.ForeignKey(
        WritingSubmission, on_delete=models.CASCADE, related_name="grammar_errors"
    )
    fragment = models.CharField(max_length=500)
    suggestion = models.CharField(max_length=500, blank=True, default="")
    short_description = models.CharField(max_length=500, blank=True, default="")
    rule_id = models.CharField(max_length=128, blank=True, default="")
    category = models.CharField(max_length=128, blank=True, default="")
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()

    class Meta:
        ordering = ["start_offset"]

    def __str__(self) -> str:
        return f"GrammarError({self.rule_id}: {self.fragment!r})"
