"""
Imports the 15 picture-description Writing tasks from
apps/writing/data/answer_keys.json into the WritingTask table.

Mirrors apps.assessment.management.commands.import_questions: safe to
re-run (tasks are matched/updated by `key`, not duplicated).

The source JSON (see its own "usage_notes") only describes each scene's
objects/synonyms/position/attributes/action - it has no ready-made student-
facing instruction text or target CEFR level, so this command generates a
straightforward default prompt per scene. Both the prompt and target_level
can be edited afterwards via the Django admin or the
/api/v1/writing/admin/tasks/ endpoints - re-running this command will NOT
overwrite a prompt that has already been customized (only expected_vocabulary
and title are always kept in sync with the JSON, since those are the answer
key, not editorial content).

Expects the matching SVG file for each scene to already exist at
apps/writing/static/writing/scenes/<key>.svg (checked, not copied - the SVGs
are checked into the app's static/ directory directly, see
apps/writing/static/writing/scenes/README.md).
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.writing.models import WritingTask

APP_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = APP_DIR / "data" / "answer_keys.json"
SCENES_DIR = APP_DIR / "static" / "writing" / "scenes"

DEFAULT_MIN_WORD_COUNT = 60


def _default_prompt(title: str, min_word_count: int) -> str:
    return (
        f"Look at the picture (\"{title}\") and describe what you see. "
        f"Write at least {min_word_count} words. Mention the objects in the "
        "picture, where they are, and what is happening."
    )


class Command(BaseCommand):
    help = (
        "Imports the picture-description Writing tasks (answer_keys.json + "
        "matching SVG scenes) into the WritingTask table. Safe to re-run: "
        "existing tasks are matched/updated by `key`, not duplicated. "
        "A prompt/target_level customized after import is preserved on re-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-word-count",
            type=int,
            default=DEFAULT_MIN_WORD_COUNT,
            help=f"min_word_count used for newly-created tasks (default: {DEFAULT_MIN_WORD_COUNT}).",
        )

    def handle(self, *args, **options):
        if not DATA_PATH.exists():
            raise CommandError(f"answer_keys.json not found: {DATA_PATH}")

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        min_word_count = options["min_word_count"]
        created, updated, missing_svg = 0, 0, []

        for order, scene in enumerate(data.get("scenes", [])):
            key = scene["id"]
            svg_path = SCENES_DIR / f"{key}.svg"
            if not svg_path.exists():
                missing_svg.append(key)

            existing = WritingTask.objects.filter(key=key).first()
            defaults = {
                "title": scene.get("title", key),
                "expected_vocabulary": scene.get("objects", []),
                "order": order,
            }
            if existing is None:
                defaults["prompt"] = _default_prompt(scene.get("title", key), min_word_count)
                defaults["min_word_count"] = min_word_count

            _, was_created = WritingTask.objects.update_or_create(key=key, defaults=defaults)
            created += int(was_created)
            updated += int(not was_created)

        if missing_svg:
            self.stdout.write(
                self.style.WARNING(
                    "Warning: no SVG file found for these task keys (expected in "
                    f"{SCENES_DIR}): {', '.join(missing_svg)}. The task was still "
                    "imported, but its picture will not render until the SVG is added."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Writing task import complete. Created: {created}, updated: {updated}, "
                f"total in DB: {WritingTask.objects.count()}."
            )
        )
