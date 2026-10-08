"""
Django settings for the LingoLab backend.

SQLite locally by default; production-safe (env-driven SECRET_KEY/DEBUG/
ALLOWED_HOSTS/CORS, PostgreSQL via DATABASE_URL, WhiteNoise static files,
auth throttling) when DEBUG=False. See apps/api/README.md §7.
"""

import os
from pathlib import Path
from datetime import timedelta

import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
_DEV_INSECURE_SECRET_KEY = "dev-insecure-secret-key-change-me"

SECRET_KEY = os.getenv("SECRET_KEY", _DEV_INSECURE_SECRET_KEY)
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",") if h.strip()]

# Fail fast instead of silently deploying an insecure configuration:
# if DEBUG is off (i.e. this is meant to run in staging/production), the
# environment MUST provide a real secret key and explicit allowed hosts.
if not DEBUG:
    if SECRET_KEY == _DEV_INSECURE_SECRET_KEY:
        raise ImproperlyConfigured(
            "SECRET_KEY env var must be set to a real secret when DEBUG=False."
        )
    if ALLOWED_HOSTS in ([], ["*"]):
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS env var must be set to explicit host(s) when DEBUG=False."
        )

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "corsheaders",
    # Local apps
    "apps.accounts",
    "apps.assessment",
    "apps.writing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database - SQLite by default (local dev / Sprint 1 default), or PostgreSQL
# (or anything else dj-database-url supports) in staging/production by
# setting DATABASE_URL, e.g.:
#   DATABASE_URL=postgres://user:password@host:5432/lingolab
# No application code depends on which engine is active.
# ---------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# In dev (DEBUG=True) and with no CORS_ALLOWED_ORIGINS set, keep it open so
# the frontend can integrate freely without extra setup. In production this
# must be an explicit, comma-separated allow-list via env, e.g.:
#   CORS_ALLOWED_ORIGINS=https://lingolab.example.com,https://app.lingolab.example.com
_cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]

if not DEBUG and not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured(
        "CORS_ALLOWED_ORIGINS env var must be set to explicit origin(s) when DEBUG=False."
    )

CORS_ALLOW_ALL_ORIGINS = DEBUG and not CORS_ALLOWED_ORIGINS

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    # Only the auth entry points below opt in (via `throttle_scope`), so
    # every other endpoint is unaffected. Guards against brute-force on
    # /login/ and abuse/spam of /signup/ and /guest/ (each guest account
    # is a free, password-less row). Values are conservative defaults,
    # overridable via env without touching code.
    "DEFAULT_THROTTLE_RATES": {
        "auth-login": os.getenv("THROTTLE_RATE_LOGIN", "10/min"),
        "auth-signup": os.getenv("THROTTLE_RATE_SIGNUP", "10/min"),
        "auth-guest": os.getenv("THROTTLE_RATE_GUEST", "20/min"),
    },
}

# ---------------------------------------------------------------------------
# drf-spectacular (Swagger / OpenAPI)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "LingoLab API",
    "DESCRIPTION": (
        "REST API for LingoLab - AI-Powered Language Development Platform. "
        "Authentication, an adaptive CEFR placement-test engine "
        "(vocabulary/grammar/reading), a Writing Assessment module "
        "(spelling/grammar/vocabulary-CEFR/topic-relevance analysis of "
        "free-text submissions), and admin content/user management."
    ),
    "VERSION": "0.4.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ---------------------------------------------------------------------------
# LingoLab adaptive assessment engine settings
# ---------------------------------------------------------------------------
# How many questions are served per CEFR level in one batch.
ASSESSMENT_BATCH_SIZE = int(os.getenv("ASSESSMENT_BATCH_SIZE", "5"))
# Minimum percentage (per level) required to advance to the next level.
# Mirrors `recommended_pass_threshold_percent` from the question-bank docs.
ASSESSMENT_PASS_THRESHOLD_PERCENT = int(os.getenv("ASSESSMENT_PASS_THRESHOLD_PERCENT", "80"))

# ---------------------------------------------------------------------------
# Writing Assessment: LanguageTool (spelling/grammar) + Celery/Redis (async
# analysis). See the `languagetool`, `redis`, and `celery-worker` services
# added to docker-compose.yml, and apps/writing/README.md.
# ---------------------------------------------------------------------------
# Empty by default: with no remote server configured,
# apps.writing.services.language_check falls back to an auto-managed local
# LanguageTool instance (needs a local JRE, no Docker required - good for
# bare `manage.py runserver` dev). Set this (docker-compose already does)
# to point at a real self-hosted server instead, e.g. in staging/production.
LANGUAGETOOL_SERVER_URL = os.getenv("LANGUAGETOOL_SERVER_URL", "")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
# No result backend: nothing in this codebase ever calls `.get()` or
# checks `AsyncResult` on a Celery task - completion/results are always
# read from our own `WritingSubmission.status`/`WritingResult` rows in the
# DB instead, which `analyze_writing_submission` updates itself. Combined
# with CELERY_TASK_IGNORE_RESULT below, this means Celery never has to
# open a Redis connection just to *track* a task's result - only the
# broker connection (for enqueueing) is actually needed, and that's fully
# skipped in WRITING_EAGER_MODE. Without this, even eager mode would try
# to reach Redis (for result tracking) and fail with a ConnectionError if
# Redis isn't running locally.
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
# Local dev convenience only: WRITING_EAGER_MODE=1 runs the analysis task
# synchronously in-process (no Redis/worker needed) - never set this in
# staging/production, see apps/writing/README.md.
CELERY_TASK_ALWAYS_EAGER = os.getenv("WRITING_EAGER_MODE", "0") == "1"
CELERY_TASK_EAGER_PROPAGATES = True
