# Hand-written to match apps/writing/models.py exactly (see the note in
# apps/api/README.md, "Writing Assessment" section, about regenerating this
# migration with `manage.py makemigrations writing --check` once dependencies
# are installed - it should produce no further changes if this file is correct).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

CEFR_CHOICES = [
    ("A1", "Beginner"),
    ("A2", "Elementary"),
    ("B1", "Intermediate"),
    ("B2", "Upper-Intermediate"),
    ("C1", "Advanced"),
    ("C2", "Proficiency / Mastery"),
]


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WritingTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "key",
                    models.SlugField(
                        max_length=64,
                        unique=True,
                        help_text=(
                            "Matches the scene id in answer_keys.json and the SVG filename "
                            "stem in apps/writing/static/writing/scenes/ (e.g. "
                            "'01_house_and_garden')."
                        ),
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("prompt", models.TextField(help_text="Instructions shown to the student above the writing editor.")),
                (
                    "target_level",
                    models.CharField(
                        blank=True,
                        choices=CEFR_CHOICES,
                        help_text="Suggested CEFR level for this task, if any.",
                        max_length=2,
                        null=True,
                    ),
                ),
                (
                    "min_word_count",
                    models.PositiveIntegerField(
                        default=40, help_text="Soft minimum shown to the student as writing guidance."
                    ),
                ),
                (
                    "expected_vocabulary",
                    models.JSONField(
                        default=list,
                        help_text=(
                            "Copy of this scene's 'objects' list from answer_keys.json "
                            "(name/synonyms/count/position/attributes/action per object). "
                            "Used by services/relevance.py for topic-relevance analysis."
                        ),
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["order", "key"],
            },
        ),
        migrations.CreateModel(
            name="WritingSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("submitted_text", models.TextField(help_text="Text written by the user.")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=12,
                    ),
                ),
                (
                    "error_message",
                    models.TextField(
                        blank=True, default="", help_text="Populated if analysis failed (status=failed)."
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="submissions",
                        to="writing.writingtask",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="writing_submissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="WritingResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "overall_score",
                    models.PositiveSmallIntegerField(
                        help_text="0-100 helper metric for the UI (progress bar etc.), not a standalone verdict."
                    ),
                ),
                ("overall_cefr_level", models.CharField(choices=CEFR_CHOICES, max_length=2)),
                (
                    "confidence",
                    models.CharField(
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
                        default="medium",
                        max_length=6,
                    ),
                ),
                ("rationale", models.TextField(blank=True, default="")),
                ("word_count", models.PositiveIntegerField(default=0)),
                ("sentence_count", models.PositiveIntegerField(default=0)),
                (
                    "vocabulary_distribution",
                    models.JSONField(default=dict, help_text='e.g. {"A1": 25, "A2": 35, ..., "unknown": 5}.'),
                ),
                (
                    "dominant_vocabulary_level",
                    models.CharField(
                        blank=True,
                        choices=CEFR_CHOICES,
                        max_length=2,
                        null=True,
                        help_text=(
                            "The single most frequent CEFR level in vocabulary_distribution "
                            "(excluding 'unknown'). Deliberately distinct from "
                            "lexical_complexity_level (a weighted average) - see "
                            "services/vocabulary.py."
                        ),
                    ),
                ),
                (
                    "lexical_complexity_level",
                    models.CharField(blank=True, choices=CEFR_CHOICES, max_length=2, null=True),
                ),
                (
                    "grammar_accuracy_level",
                    models.CharField(blank=True, choices=CEFR_CHOICES, max_length=2, null=True),
                ),
                (
                    "grammar_complexity_level",
                    models.CharField(blank=True, choices=CEFR_CHOICES, max_length=2, null=True),
                ),
                (
                    "topic_relevance",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("relevant", "Relevant"),
                            ("partially_relevant", "Partially relevant"),
                            ("weakly_relevant", "Weakly relevant"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                (
                    "topic_relevance_details",
                    models.JSONField(
                        default=dict,
                        help_text=(
                            "matched_objects/total_core_objects, matched keyword list, "
                            "bonus position/attribute/action matches - see services/relevance.py."
                        ),
                    ),
                ),
                ("strengths", models.JSONField(default=list)),
                ("weaknesses", models.JSONField(default=list)),
                ("feedback", models.TextField(blank=True, default="")),
                (
                    "limitations",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Explicit description of the method's limitations - always populated.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "submission",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="result",
                        to="writing.writingsubmission",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SpellingError",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("word", models.CharField(max_length=255)),
                ("suggestion", models.CharField(blank=True, default="", max_length=255)),
                (
                    "error_type",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Rule category from the analyzer (e.g. MORFOLOGIK_RULE_EN_US).",
                        max_length=64,
                    ),
                ),
                ("start_offset", models.PositiveIntegerField()),
                ("end_offset", models.PositiveIntegerField()),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="spelling_errors",
                        to="writing.writingsubmission",
                    ),
                ),
            ],
            options={
                "ordering": ["start_offset"],
            },
        ),
        migrations.CreateModel(
            name="GrammarError",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fragment", models.CharField(max_length=500)),
                ("suggestion", models.CharField(blank=True, default="", max_length=500)),
                ("short_description", models.CharField(blank=True, default="", max_length=500)),
                ("rule_id", models.CharField(blank=True, default="", max_length=128)),
                ("category", models.CharField(blank=True, default="", max_length=128)),
                ("start_offset", models.PositiveIntegerField()),
                ("end_offset", models.PositiveIntegerField()),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grammar_errors",
                        to="writing.writingsubmission",
                    ),
                ),
            ],
            options={
                "ordering": ["start_offset"],
            },
        ),
        migrations.AddIndex(
            model_name="writingsubmission",
            index=models.Index(fields=["user", "-created_at"], name="writing_wri_user_id_1b6f16_idx"),
        ),
        migrations.AddIndex(
            model_name="writingsubmission",
            index=models.Index(fields=["status"], name="writing_wri_status_4a5e26_idx"),
        ),
    ]
