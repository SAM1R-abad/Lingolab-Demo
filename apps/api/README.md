# LingoLab Backend

Backend for **LingoLab**, an AI-powered adaptive English learning platform.
Core piece: **the adaptive engine that evaluates a learner and
automatically adjusts exercise difficulty (CEFR level) based on
performance**, plus authentication, an admin-managed question bank (three
skills: vocabulary/grammar/reading), a **Writing Assessment module**
(free-text picture-description tasks with spelling/grammar/vocabulary-CEFR/
topic-relevance analysis - see §4a), and full OpenAPI/Swagger documentation.

Stack: **Python / Django / Django REST Framework**, **SQLite** for local
dev / **PostgreSQL**-ready for staging & production (see §7), **WhiteNoise**
for static files, **gunicorn** as the app server, **drf-spectacular**
(Swagger/OpenAPI), plus **Celery/Redis/LanguageTool** for the Writing
Assessment module specifically (see `apps/writing/README.md`).

---

## 1. Project structure

```
apps/api/
├── manage.py
├── requirements.txt
├── .env.example
├── config/                    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── apps/
    ├── accounts/               # Sign Up / Login (simple, non-hardened for Sprint 1)
    │   ├── models.py           # Custom User model (role field for future use)
    │   ├── serializers.py
    │   ├── views.py
    │   └── urls.py
    ├── assessment/             # ⭐ Core module: adaptive CEFR placement test
    │   ├── models.py           # Question, PlacementSession, SessionQuestion
    │   ├── services.py         # AdaptiveEngine — the adaptive algorithm itself
    │   ├── serializers.py
    │   ├── views.py
    │   ├── urls.py
    │   ├── data/                       # Provided question banks (477 questions)
    │   │   ├── cefr_vocabulary_test.json
    │   │   └── cefr_grammar_test.json
    │   └── management/commands/
    │       └── import_questions.py     # Loads the JSON banks into the DB
    └── writing/                # Writing Assessment (picture-description tasks) - see apps/writing/README.md
        ├── models.py           # WritingTask, WritingSubmission, WritingResult, SpellingError, GrammarError
        ├── services/           # pipeline.py (entry point), language_check.py, vocabulary.py,
        │                       # grammar_complexity.py, relevance.py, scoring.py, persistence.py, nlp.py
        ├── tasks.py            # Celery task: analyze_writing_submission
        ├── serializers.py
        ├── views.py
        ├── urls.py
        ├── data/answer_keys.json           # 15 scenes' expected vocabulary (answer key)
        ├── static/writing/scenes/*.svg     # matching SVG pictures
        └── management/commands/
            └── import_writing_tasks.py     # Loads answer_keys.json (+ SVGs) into the DB
```

## 2. Setup & run

```bash
cd apps/api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm   # spaCy model used by the writing-assessment module

cp .env.example .env            # defaults are fine for local dev

python manage.py migrate
python manage.py import_questions   # loads the 477 CEFR questions into SQLite
python manage.py import_writing_tasks   # loads the 15 Writing picture-description tasks
python manage.py collectstatic --noinput   # required: serves the writing-task SVG scenes
python manage.py createsuperuser    # optional, for /admin/

python manage.py runserver
```

Writing Assessment needs LanguageTool + Redis + a Celery worker to actually
analyze submissions - either run `docker-compose up` from the repo root
(which starts all of it), or set `WRITING_EAGER_MODE=1` in `.env` for local-
only synchronous analysis without that extra infrastructure. See
`apps/writing/README.md` for details.

The API is now available at `http://127.0.0.1:8000/`.

- Swagger UI: **http://127.0.0.1:8000/api/docs/**
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- Raw OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- Django admin: `http://127.0.0.1:8000/admin/`

## 3. Authentication

Sprint 1 uses DRF's built-in **Token Authentication** — a deliberately
simple structure (no JWT, no email verification, no rate limiting), as
agreed for the MVP. Every endpoint except `signup`/`login` requires the
header:

```
Authorization: Token <token>
```

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/signup/` | Register a new user, returns `{user, token}` |
| POST | `/api/v1/auth/login/` | Log in, returns `{user, token}` |
| POST | `/api/v1/auth/guest/` | Create a temporary, password-less guest account and return `{user, token}` immediately - no form required |
| GET | `/api/v1/auth/me/` | Get the current authenticated user |
| PATCH | `/api/v1/auth/me/` | Update your own `first_name` / `last_name` / `email` |
| DELETE | `/api/v1/auth/me/` | Permanently delete your own account |
| GET | `/api/v1/auth/users/` | **Admin only.** List all users |
| GET/PATCH/DELETE | `/api/v1/auth/users/{id}/` | **Admin only.** View, update (e.g. `role`, `is_active`), or delete any user |

## 4. Adaptive placement test API (core module)

The engine lives in `apps/assessment/services.py` (`AdaptiveEngine`).
Algorithm, in short:

1. Start at CEFR level **A1**.
2. Serve a batch of `ASSESSMENT_BATCH_SIZE` (default 5) random questions
   at the current level, for the chosen skill (`vocabulary` or `grammar`).
3. Once the batch is fully answered, score it.
4. If score **≥ `ASSESSMENT_PASS_THRESHOLD_PERCENT`** (default 80%, per
   `cefr_test_json_documentation.md`): mark the level passed and move to
   the next level with a new batch — or finish with result `C2` if that
   was the top level.
5. Otherwise: finish the session. `result_level` = highest level passed
   so far, or `"Pre-A1"` if even A1 was not passed.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/assessment/start/` | Body: `{"skill": "vocabulary"\|"grammar"}`. Creates a session and returns the first (A1) batch. |
| POST | `/api/v1/assessment/{id}/answer/` | Body: `{"question_id": int, "answer": "<option text>"}`. Submits one answer; when the batch is complete the response includes either the next batch or the final `result`. |
| GET | `/api/v1/assessment/{id}/` | Current session status + current batch. |
| GET | `/api/v1/assessment/{id}/result/` | Final result + per-level score breakdown (only once `status == "completed"`). |
| GET | `/api/v1/assessment/sessions/` | List all of the current user's past and in-progress sessions (used by the Progress screen). |
| GET | `/api/v1/assessment/levels/` | Static `{code: name}` lookup for CEFR levels, e.g. `{"A1": "Beginner", ...}`. |
| GET/POST | `/api/v1/assessment/questions/` | **Admin only.** List (with optional `?skill=&level=` filters) or create questions - full content management, complementing `import_questions`. |
| GET/PATCH/DELETE | `/api/v1/assessment/questions/{id}/` | **Admin only.** View, edit, or delete a single question. |

Question objects sent to the client **never include `correct_answer`**.

### Example flow

```bash
# 1. Sign up
curl -X POST localhost:8000/api/v1/auth/signup/ -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"pass1234","password2":"pass1234"}'
# -> {"user": {...}, "token": "abc123..."}

# 2. Start a placement test
curl -X POST localhost:8000/api/v1/assessment/start/ \
  -H "Authorization: Token abc123..." -H "Content-Type: application/json" \
  -d '{"skill": "vocabulary"}'
# -> {"session": {...}, "questions": [5 A1 questions]}

# 3. Answer each question
curl -X POST localhost:8000/api/v1/assessment/1/answer/ \
  -H "Authorization: Token abc123..." -H "Content-Type: application/json" \
  -d '{"question_id": 19, "answer": "pay money to get it"}'

# 4. Once completed, get the result
curl localhost:8000/api/v1/assessment/1/result/ -H "Authorization: Token abc123..."
```

## 4a. Writing Assessment (`apps.writing`)

Free-text picture-description writing tasks with automated (non-LLM,
rule/heuristic-based) analysis: spelling, grammar, vocabulary CEFR
distribution, and topic relevance. Full details, required extra
infrastructure (LanguageTool/Redis/Celery), setup steps, and the method's
explicit limitations are documented in **`apps/writing/README.md`** -
read that before touching this module.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/writing/tasks/` | List active writing tasks (prompt + SVG picture, no answer key). |
| GET | `/api/v1/writing/tasks/{id}/` | A single task's detail. |
| GET/POST | `/api/v1/writing/submissions/` | List the current user's submissions (Progress history), or submit a new response (`{"task_id": int, "submitted_text": str}`) - schedules async analysis. |
| GET | `/api/v1/writing/submissions/{id}/` | Submission status + result once ready (poll until `status` is `completed`/`failed`). |
| GET | `/api/v1/writing/submissions/{id}/result/` | Just the result payload (400 until completed). |
| GET/POST | `/api/v1/writing/admin/tasks/` | **Admin only.** List/create tasks with the full answer key, complementing `import_writing_tasks`. |
| GET/PATCH/DELETE | `/api/v1/writing/admin/tasks/{id}/` | **Admin only.** View, edit, or delete a task. |

## 5. Data model notes

- `Question.external_id` is unique **per skill** (`vocabulary` and
  `grammar` question banks reuse the same id scheme, e.g. both contain
  a `"B2-014"`), so the uniqueness constraint is `(skill, external_id)`.
- `Skill` declares `reading`, `listening`, `speaking`, `writing` in
  addition to `vocabulary`/`grammar`. As of Sprint 3, **`reading` is
  fully implemented** (model, `import_questions`, ~54 questions, and a
  working frontend skill-selection flow) alongside vocabulary and
  grammar - it's no longer just a placeholder value. `listening` and
  `speaking` remain unimplemented, future-sprint skills. `writing` as a
  `Skill` value is likewise still unused by the adaptive placement engine -
  but free-text Writing Assessment itself is now implemented as its own
  app (`apps.writing`, see §4a), deliberately *not* wired into
  `PlacementSession`/`Skill` since it isn't a multiple-choice adaptive test.
- `manage.py import_questions` is idempotent — safe to re-run after
  updating the JSON files; it upserts by `(skill, external_id)`.

## 6. What's intentionally out of scope for Sprint 3

- No JWT/refresh tokens — token auth only, documented trade-off for MVP.
- No email verification.
- Teacher role: the `role` field/value exists, but no teacher-specific
  permission class or endpoint is implemented (only `IsAdmin` / regular
  user). Deliberately deferred, not a Sprint 3 blocker.
- Full test suite / CI pipeline.

## 7. Production deployment (Sprint 3)

The app is now deployment-ready (not yet deployed by default):

- `DATABASE_URL` env var switches from local SQLite to PostgreSQL (or any
  `dj-database-url`-supported engine) with no code changes - see
  `config/settings.py` and `.env.example`.
- `DEBUG=False` enforces production-safe config at startup: it refuses to
  boot with the default `SECRET_KEY`, `ALLOWED_HOSTS=*`, or an unset
  `CORS_ALLOWED_ORIGINS`.
- Static files are served via WhiteNoise (`collectstatic` run at build
  time in the Dockerfile).
- Auth endpoints (`/signup/`, `/login/`, `/guest/`) are rate-limited via
  DRF `ScopedRateThrottle`, tunable via `THROTTLE_RATE_*` env vars.
- `Dockerfile` + `Procfile` are provided (`Procfile` for a buildpack-style
  PaaS such as Render/Railway/Heroku; `Dockerfile` for anywhere else,
  including the root `docker-compose.yml` used for a local smoke test of
  this exact setup with real PostgreSQL).
