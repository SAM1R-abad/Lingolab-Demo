from __future__ import annotations

from django.templatetags.static import static
from rest_framework import serializers

from apps.writing.models import (
    GrammarError,
    SpellingError,
    WritingResult,
    WritingSubmission,
    WritingTask,
)


class WritingTaskSerializer(serializers.ModelSerializer):
    """Public task representation shown to the student (no answer key)."""

    svg_url = serializers.SerializerMethodField()

    class Meta:
        model = WritingTask
        fields = (
            "id",
            "key",
            "title",
            "prompt",
            "target_level",
            "min_word_count",
            "svg_url",
        )

    def get_svg_url(self, obj: WritingTask) -> str:
        path = static(obj.svg_static_path)
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path


class WritingTaskAdminSerializer(serializers.ModelSerializer):
    """Full task representation for admin CRUD, includes the answer key."""

    class Meta:
        model = WritingTask
        fields = (
            "id",
            "key",
            "title",
            "prompt",
            "target_level",
            "min_word_count",
            "expected_vocabulary",
            "is_active",
            "order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class WritingSubmissionCreateSerializer(serializers.ModelSerializer):
    """Input payload for creating a new submission to be analyzed."""

    task_id = serializers.PrimaryKeyRelatedField(
        source="task", queryset=WritingTask.objects.filter(is_active=True)
    )

    class Meta:
        model = WritingSubmission
        fields = ["id", "task_id", "submitted_text", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate_submitted_text(self, value: str) -> str:
        text = value.strip()
        if not text:
            raise serializers.ValidationError("The text to analyze cannot be empty.")
        if len(text) < 10:
            raise serializers.ValidationError(
                "The text is too short for a meaningful analysis (minimum 10 characters)."
            )
        if len(text) > 20000:
            raise serializers.ValidationError(
                "The text is too long (maximum 20,000 characters per submission)."
            )
        return text


class SpellingErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpellingError
        fields = ["word", "suggestion", "error_type", "start_offset", "end_offset"]


class GrammarErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarError
        fields = [
            "fragment",
            "suggestion",
            "short_description",
            "rule_id",
            "category",
            "start_offset",
            "end_offset",
        ]


class WritingResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingResult
        fields = [
            "overall_score",
            "overall_cefr_level",
            "confidence",
            "rationale",
            "word_count",
            "sentence_count",
            "vocabulary_distribution",
            "dominant_vocabulary_level",
            "lexical_complexity_level",
            "grammar_accuracy_level",
            "grammar_complexity_level",
            "topic_relevance",
            "topic_relevance_details",
            "strengths",
            "weaknesses",
            "feedback",
            "limitations",
        ]


class WritingSubmissionDetailSerializer(serializers.ModelSerializer):
    """
    Full response for one submission: status + task snapshot + (once ready)
    the analysis result with spelling/grammar error lists.
    """

    task = WritingTaskSerializer(read_only=True)
    result = WritingResultSerializer(read_only=True)
    spelling_errors = SpellingErrorSerializer(many=True, read_only=True)
    grammar_errors = GrammarErrorSerializer(many=True, read_only=True)

    class Meta:
        model = WritingSubmission
        fields = [
            "id",
            "task",
            "submitted_text",
            "status",
            "error_message",
            "created_at",
            "completed_at",
            "result",
            "spelling_errors",
            "grammar_errors",
        ]


class WritingSubmissionListSerializer(serializers.ModelSerializer):
    """Lightweight version for the history/Progress list (no error detail)."""

    task_title = serializers.CharField(source="task.title", read_only=True)
    overall_cefr_level = serializers.CharField(source="result.overall_cefr_level", read_only=True, default=None)
    overall_score = serializers.IntegerField(source="result.overall_score", read_only=True, default=None)

    class Meta:
        model = WritingSubmission
        fields = [
            "id",
            "task_title",
            "status",
            "created_at",
            "completed_at",
            "overall_cefr_level",
            "overall_score",
        ]
