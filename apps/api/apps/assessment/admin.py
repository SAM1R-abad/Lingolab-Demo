from django.contrib import admin

from .models import PlacementSession, Question, SessionQuestion


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("external_id", "skill", "level", "question_type", "tag")
    list_filter = ("skill", "level", "question_type")
    search_fields = ("external_id", "prompt", "tag")


class SessionQuestionInline(admin.TabularInline):
    model = SessionQuestion
    extra = 0
    readonly_fields = ("question", "level", "order", "selected_answer", "is_correct", "answered_at")
    can_delete = False


@admin.register(PlacementSession)
class PlacementSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "skill", "status", "current_level", "result_level", "created_at")
    list_filter = ("skill", "status", "result_level")
    inlines = (SessionQuestionInline,)
