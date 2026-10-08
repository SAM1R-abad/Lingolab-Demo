import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.assessment.models import Question, Skill

APP_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Separator used to join a reading passage with its comprehension question
# inside `Question.prompt` (the model has no separate "passage" column, so
# the passage travels inside the same text field). The web app's
# `splitReadingPrompt` helper (apps/web/src/lib/utils.ts) looks for this
# exact marker to render the passage and the question separately - keep
# the two in sync if this ever changes.
READING_PASSAGE_SEPARATOR = "\n\n[[READING_QUESTION]]\n\n"

# Which source JSON file maps to which Skill + which field holds the topic tag.
DEFAULT_SOURCES = [
    {
        "path": APP_DATA_DIR / "cefr_vocabulary_test.json",
        "skill": Skill.VOCABULARY,
        "tag_field": "word_tested",
    },
    {
        "path": APP_DATA_DIR / "cefr_grammar_test.json",
        "skill": Skill.GRAMMAR,
        "tag_field": "grammar_point",
    },
    {
        "path": APP_DATA_DIR / "cefr_reading_test.json",
        "skill": Skill.READING,
        "tag_field": "reading_topic",
    },
]


def _build_prompt(q: dict) -> str:
    """
    Vocabulary/grammar questions only have a "question" field, so their
    prompt is unchanged. Reading questions additionally have a "passage"
    field, which is prepended using READING_PASSAGE_SEPARATOR so the
    frontend can display the passage above the question.
    """
    passage = q.get("passage")
    if passage:
        return f"{passage}{READING_PASSAGE_SEPARATOR}{q['question']}"
    return q["question"]


class Command(BaseCommand):
    help = (
        "Imports the CEFR vocabulary, grammar, and reading question banks "
        "(JSON files, see cefr_test_json_documentation.md) into the Question "
        "table. Safe to re-run: existing questions are updated by "
        "`external_id`, not duplicated."
    )

    def handle(self, *args, **options):
        created, updated = 0, 0

        for source in DEFAULT_SOURCES:
            path: Path = source["path"]
            if not path.exists():
                raise CommandError(f"Question bank file not found: {path}")

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            levels = data.get("levels", {})
            for level, questions in levels.items():
                for q in questions:
                    _, was_created = Question.objects.update_or_create(
                        skill=source["skill"],
                        external_id=q["id"],
                        defaults={
                            "level": level,
                            "question_type": q.get("type", ""),
                            "prompt": _build_prompt(q),
                            "options": q["options"],
                            "correct_answer": q["correct_answer"],
                            "tag": q.get(source["tag_field"], ""),
                        },
                    )
                    created += int(was_created)
                    updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Question bank import complete. Created: {created}, updated: {updated}, "
                f"total in DB: {Question.objects.count()}."
            )
        )
