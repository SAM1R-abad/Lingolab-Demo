from __future__ import annotations

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.writing.models import WritingTask


class ImportWritingTasksCommandTests(TestCase):
    def test_imports_all_scenes_from_answer_keys_json(self):
        call_command("import_writing_tasks", stdout=StringIO())
        self.assertEqual(WritingTask.objects.count(), 15)
        self.assertTrue(WritingTask.objects.filter(key="01_house_and_garden").exists())

    def test_is_safe_to_rerun_without_duplicating(self):
        call_command("import_writing_tasks", stdout=StringIO())
        call_command("import_writing_tasks", stdout=StringIO())
        self.assertEqual(WritingTask.objects.count(), 15)

    def test_rerun_preserves_manually_edited_prompt(self):
        call_command("import_writing_tasks", stdout=StringIO())
        task = WritingTask.objects.get(key="01_house_and_garden")
        task.prompt = "A custom, teacher-edited prompt."
        task.save(update_fields=["prompt"])

        call_command("import_writing_tasks", stdout=StringIO())

        task.refresh_from_db()
        self.assertEqual(task.prompt, "A custom, teacher-edited prompt.")

    def test_rerun_keeps_expected_vocabulary_in_sync_with_json(self):
        call_command("import_writing_tasks", stdout=StringIO())
        task = WritingTask.objects.get(key="01_house_and_garden")
        self.assertTrue(len(task.expected_vocabulary) > 0)
        original_vocab = task.expected_vocabulary

        call_command("import_writing_tasks", stdout=StringIO())
        task.refresh_from_db()
        self.assertEqual(task.expected_vocabulary, original_vocab)

    def test_every_imported_task_has_a_matching_svg_file(self):
        from pathlib import Path

        call_command("import_writing_tasks", stdout=StringIO())
        scenes_dir = Path(__file__).resolve().parent.parent / "static" / "writing" / "scenes"
        for task in WritingTask.objects.all():
            self.assertTrue((scenes_dir / f"{task.key}.svg").exists(), f"missing SVG for {task.key}")
