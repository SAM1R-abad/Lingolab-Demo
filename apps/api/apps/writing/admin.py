from django.contrib import admin

from .models import GrammarError, SpellingError, WritingResult, WritingSubmission, WritingTask


@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "target_level", "min_word_count", "is_active", "order")
    list_filter = ("target_level", "is_active")
    search_fields = ("key", "title", "prompt")
    ordering = ("order", "key")


class SpellingErrorInline(admin.TabularInline):
    model = SpellingError
    extra = 0
    readonly_fields = ("word", "suggestion", "error_type", "start_offset", "end_offset")
    can_delete = False


class GrammarErrorInline(admin.TabularInline):
    model = GrammarError
    extra = 0
    readonly_fields = (
        "fragment",
        "suggestion",
        "short_description",
        "rule_id",
        "category",
        "start_offset",
        "end_offset",
    )
    can_delete = False


class WritingResultInline(admin.StackedInline):
    model = WritingResult
    extra = 0
    can_delete = False
    readonly_fields = (
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
    )


@admin.register(WritingSubmission)
class WritingSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "task", "status", "created_at", "completed_at")
    list_filter = ("status", "task")
    search_fields = ("user__username", "submitted_text")
    inlines = (WritingResultInline, SpellingErrorInline, GrammarErrorInline)
