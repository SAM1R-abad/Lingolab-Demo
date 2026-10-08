# Writing Assessment (`apps.writing`)

Picture-description writing tasks: a student sees an SVG scene and a
prompt, writes a free-text response, and gets an automated (non-LLM,
rule/heuristic-based) analysis of spelling, grammar, vocabulary CEFR level,
and topic relevance.

This module was integrated from a standalone prototype (`writing_assessment`)
plus a set of picture/answer-key materials (`writing materials`). See the
architecture discussion in the project history for the full rationale; this
file covers what you need to run and maintain it day to day.

## Architecture at a glance

```
POST /api/v1/writing/submissions/  (task_id + submitted_text)
        |
        v
WritingSubmission (status=pending) saved
        |
        v
analyze_writing_submission.delay(submission_id)   <- Celery task, async
        |
        v
services/pipeline.analyze_writing(...)
    |-- services/language_check.check_text(...)        LanguageTool (spelling+grammar)
    |-- services/vocabulary.analyze_vocabulary(...)     spaCy + cefrpy  (CEFR distribution)
    |-- services/grammar_complexity.analyze_grammar_complexity(...)   spaCy (heuristic)
    |-- services/relevance.analyze_relevance(...)       spaCy lemmas vs answer_keys.json
    `-- services/scoring.compute_overall_assessment(...) combines the above
        |
        v
services/persistence.persist_analysis_result(...) -> WritingResult + SpellingError/GrammarError rows
        |
        v
WritingSubmission.status = completed
```

The pipeline (`services/pipeline.py`) is pure/ORM-free by design: it takes
plain values in and returns a plain `WritingAnalysisResult` dataclass, so it
stays unit-testable without a database and reusable outside Celery later
(e.g. a future batch-reanalysis command, or a future LLM-based evaluation
stage layered on top - see the module docstrings for where that would slot
in).

## Required infrastructure (this module, specifically)

Two ways to run this locally:

**Option A - full stack via Docker (`docker-compose up`).** Unlike the rest
of LingoLab (which runs fine as a single Django process), Writing Assessment
then uses three extra services, all added to the root `docker-compose.yml`:

- **LanguageTool** (`languagetool` service, `erikvl87/languagetool` image) -
  self-hosted spelling/grammar checker. A Java process; budget ~1.2 GB RAM.
- **Redis** (`redis` service) - Celery broker.
- **Celery worker** (`celery-worker` service) - runs
  `apps.writing.tasks.analyze_writing_submission` outside the HTTP request
  cycle, since a full analysis (LanguageTool + spaCy + cefrpy) is too slow to
  do synchronously inside a web request.

**Option B - bare `manage.py runserver`, no Docker at all.** This is what
`.env.example` is set up for by default:

- `LANGUAGETOOL_SERVER_URL=` (empty) - with no remote server configured,
  `services/language_check.py` automatically falls back to
  `language_tool_python`'s **auto-managed local LanguageTool**: it downloads
  LanguageTool (~200 MB) and runs it as a local Java process on first use,
  then reuses it. **Requires a local Java 17+ runtime on `PATH`** - install
  a JRE first (e.g. Temurin/OpenJDK) or you'll get a clear `LanguageCheckError`
  (not a 500 - see the note about `WritingSubmission.status=failed` below).
  The first submission after startup will be noticeably slow (downloading +
  starting the JVM); later ones are fast.
- `WRITING_EAGER_MODE=1` - runs the analysis task synchronously in-process,
  so no Redis/Celery worker is needed either. **Never set this in staging or
  production** - it defeats the entire point of the async pipeline and will
  make writing submissions block a web worker for several seconds each.

Environment variables (see `.env.example`):

- `LANGUAGETOOL_SERVER_URL` - empty by default (Option B, above);
  `http://languagetool:8010` in docker-compose (Option A).
- `CELERY_BROKER_URL` - defaults to `redis://localhost:6379/0`, only used
  when `WRITING_EAGER_MODE=0`; `redis://redis:6379/0` in docker-compose.
- `WRITING_EAGER_MODE` - `1` by default in `.env.example` (Option B); set to
  `0` when running the full docker-compose stack (Option A), where analysis
  should genuinely run async in the `celery-worker` container.

**A submission never crashes the HTTP layer, whichever option you use.**
`WritingSubmissionListCreateView.post()` wraps the `.delay()` call: if
analysis fails synchronously (only possible in eager mode, or if the Celery
broker itself is unreachable), the exception is logged, not re-raised - the
task itself already persisted `WritingSubmission.status="failed"` with a
human-readable `error_message` before that, so the frontend's existing
polling/failed-state UI picks it up normally instead of seeing an HTTP 500.

## First-time setup

```bash
# From apps/api, with the venv/requirements installed:
python -m spacy download en_core_web_sm   # not installed by `pip install spacy` itself
python manage.py migrate
python manage.py import_writing_tasks     # loads the 15 picture-description tasks
```

If you're going with Option B above, also make sure a JRE is installed and
on `PATH` (`java -version` should work) - LanguageTool needs it whether it's
auto-managed locally or running in Docker.

`import_writing_tasks` is idempotent - safe to re-run any time the source
`data/answer_keys.json` changes. It updates `title`/`expected_vocabulary`
from the JSON on every run, but preserves a `prompt`/`target_level` that has
since been hand-edited via the admin or `/api/v1/writing/admin/tasks/`.

If you regenerate `apps/writing/migrations/0001_initial.py`'s source model
(i.e. edit `models.py`), the migration file was **hand-written** to match it
exactly (no `makemigrations` was run - no network access at authoring time).
Run `python manage.py makemigrations writing --check` once you have a real
environment; it should report no changes. If it does, that means the
hand-written migration and the models drifted - regenerate the migration
properly and replace the hand-written one.

## Known limitations (by design, not bugs)

Every `WritingResult` carries a `limitations` field spelling these out to
the end user as well:

- **Spelling/grammar** (LanguageTool): rule-based, not meaning-aware. Misses
  semantically wrong-but-grammatical text; the spelling/grammar split
  depends on LanguageTool's own rule categorization.
- **Vocabulary CEFR level**: limited to the CEFR-J/Octanove wordlist
  (via `cefrpy`); anything outside it (slang, typos, proper nouns) is
  `"unknown"`, never treated as an error. A word's level is looked up by
  lemma + POS, not by the sense actually used in context.
- **`dominant_vocabulary_level` vs `lexical_complexity_level`**: these are
  deliberately different numbers - the former is the mode of the CEFR
  distribution ("most common level"), the latter is a weighted average.
  Never conflate them; a single advanced word does not make either one jump.
- **Grammar complexity**: the most heuristic part of the whole pipeline -
  estimated from spaCy dependency-parse patterns (subordinate clauses,
  passive voice, conditionals, modal variety), not a validated CEFR grammar
  classifier. Gives a direction, not a precise score.
- **Topic relevance**: keyword/lemma overlap against a task's
  `expected_vocabulary` (from `answer_keys.json`). Not semantic
  understanding. A missing keyword is never an error - keywords are
  supporting evidence only, and `count == 0` objects in the JSON are
  optional/bonus, never required.

This is a functional/demo-oriented assessment, explicitly not a certified
CEFR exam - see `services/pipeline.LIMITATIONS_TEXT`.

## Adding/editing tasks

- Via `python manage.py import_writing_tasks` (bulk, from
  `data/answer_keys.json` + `static/writing/scenes/*.svg`), or
- Via Django admin (`/admin/writing/writingtask/`), or
- Via `/api/v1/writing/admin/tasks/` (requires `IsAdmin`).

Every task's `key` must match both the scene `id` in `answer_keys.json` and
an SVG filename stem in `static/writing/scenes/` (e.g. `key="05_park"` ->
`static/writing/scenes/05_park.svg`). The import command warns (but does not
fail) if a task's SVG is missing.
