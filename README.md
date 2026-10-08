# LingoLab

Adaptive English learning platform — Django/DRF API + Next.js web app, in a
single monorepo.

**Status:** Sprint 1 (MVP Foundation) and Sprint 2 (Core Features
Integration) complete — auth (incl. guest access), adaptive CEFR placement
engine, question-bank CRUD, user profile/account CRUD, admin user
management, and the corresponding frontend for all of it.

```
lingolab-monorepo/
├── apps/
│   ├── api/     Django + DRF backend (auth, adaptive placement engine, question bank)
│   └── web/     Next.js + TypeScript frontend (KUDS-compliant UI)
└── README.md    (this file)
```

Each app is self-contained with its own dependency manager (`pip` for
`apps/api`, `npm` for `apps/web`) and its own detailed README — see
`apps/api/README.md` and `apps/web/README.md` for full setup, environment
variables, and API/route references.

## Quick start (two terminals)

**Terminal 1 — API**

```bash
cd apps/api
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # required by the writing-assessment module
cp .env.example .env
python manage.py migrate
python manage.py import_questions
python manage.py import_writing_tasks
python manage.py collectstatic --noinput  # required: serves the writing-task SVG scenes
python manage.py createsuperuser
python manage.py runserver
```

Running at **http://127.0.0.1:8000** (Swagger: `/api/docs/`).

**Terminal 2 — Web**

```bash
cd apps/web
npm install
cp .env.local.example .env.local
npm run dev
```

Running at **http://localhost:3000** — this is the site itself, talking to
the API automatically.

## Why this layout

`apps/<name>` is a standard monorepo convention: each folder under `apps/`
is an independently runnable application with its own toolchain, while the
repository root stays free for shared, cross-cutting concerns (CI config,
top-level docs, etc.) as the project grows. Python and Node.js remain
separate processes/dependency trees either way — this layout doesn't merge
them, it just organizes them the way most full-stack teams do.
