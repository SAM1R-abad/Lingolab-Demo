from django.conf import settings
from django.db import models


class CEFRLevel(models.TextChoices):
    A1 = "A1", "Beginner"
    A2 = "A2", "Elementary"
    B1 = "B1", "Intermediate"
    B2 = "B2", "Upper-Intermediate"
    C1 = "C1", "Advanced"
    C2 = "C2", "Proficiency / Mastery"

    @classmethod
    def order(cls):
        """CEFR levels sorted from lowest to highest."""
        return [cls.A1, cls.A2, cls.B1, cls.B2, cls.C1, cls.C2]


class Skill(models.TextChoices):
    """
    Skills the platform assesses. VOCABULARY, GRAMMAR, and READING have a
    ready question bank (see cefr_vocabulary_test.json /
    cefr_grammar_test.json / cefr_reading_test.json). The remaining skills
    from the project brief (Listening, Speaking, Writing) are declared here
    already so the adaptive engine and models do not need to change when
    their question banks are added in a later sprint.
    """

    VOCABULARY = "vocabulary", "Vocabulary"
    GRAMMAR = "grammar", "Grammar"
    READING = "reading", "Reading"
    LISTENING = "listening", "Listening"
    SPEAKING = "speaking", "Speaking"
    WRITING = "writing", "Writing"


class Question(models.Model):
    """
    A single multiple-choice CEFR question. Bulk-loaded from the provided
    JSON question banks via `manage.py import_questions`, and individually
    manageable by admins via the /api/v1/assessment/questions/ CRUD API
    (Sprint 2).
    """

    external_id = models.CharField(
        max_length=20,
        help_text='Original id from the source JSON, e.g. "B2-014".',
    )
    skill = models.CharField(max_length=20, choices=Skill.choices)
    level = models.CharField(max_length=2, choices=CEFRLevel.choices)
    question_type = models.CharField(
        max_length=30,
        help_text='Original "type" field from the source JSON (e.g. "meaning", "grammar").',
    )
    prompt = models.TextField(help_text="The question text shown to the test-taker.")
    options = models.JSONField(help_text="Always exactly 4 answer choices.")
    correct_answer = models.CharField(
        max_length=500,
        help_text="Exact copy of the correct string from `options`.",
    )
    tag = models.CharField(
        max_length=255,
        blank=True,
        help_text="word_tested (vocabulary) or grammar_point (grammar).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["skill", "external_id"], name="unique_external_id_per_skill"
            )
        ]
        indexes = [models.Index(fields=["skill", "level"])]
        ordering = ["skill", "level", "external_id"]

    def __str__(self):
        return f"[{self.skill}] {self.external_id}"


class PlacementSession(models.Model):
    """
    One adaptive placement-test attempt for a single skill.

    Adaptive logic (see apps.assessment.services.AdaptiveEngine):
    the test starts at A1 and serves one batch of questions per level.
    If the test-taker scores >= ASSESSMENT_PASS_THRESHOLD_PERCENT on a
    level, the engine advances to the next level; otherwise the session
    ends and the result is the highest level passed so far.
    """

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="placement_sessions"
    )
    skill = models.CharField(max_length=20, choices=Skill.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    current_level = models.CharField(max_length=2, choices=CEFRLevel.choices, default=CEFRLevel.A1)
    passed_levels = models.JSONField(
        default=list, help_text="CEFR levels that scored >= threshold, in order."
    )
    result_level = models.CharField(
        max_length=10,
        blank=True,
        help_text='Final assessed level, e.g. "B1", or "Pre-A1" if A1 was not passed.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session #{self.pk} ({self.user}, {self.skill}, {self.status})"


class SessionQuestion(models.Model):
    """
    A question served to the user within a specific placement session,
    together with their answer (once submitted). This is what lets the
    adaptive engine score a level batch and prevents the same question
    from being served twice in one session.
    """

    session = models.ForeignKey(
        PlacementSession, on_delete=models.CASCADE, related_name="session_questions"
    )
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    level = models.CharField(max_length=2, choices=CEFRLevel.choices)
    order = models.PositiveSmallIntegerField()
    selected_answer = models.CharField(max_length=500, blank=True)
    is_correct = models.BooleanField(null=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("session", "question")
        ordering = ["session", "level", "order"]

    def __str__(self):
        return f"Session #{self.session_id} - Q{self.question_id}"
