FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# psycopg2-binary wheels cover most platforms, but keep build tools around
# in case the target platform needs to build from source.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    # spaCy's small English model is used by the Writing Assessment module
    # (apps/writing) for vocabulary/grammar-complexity analysis. It is not
    # installed by `pip install spacy` itself and must be fetched separately.
    && python -m spacy download en_core_web_sm

COPY . .

# Static files are collected at build time (needs a real SECRET_KEY only if
# DEBUG=False; DEBUG is not set here, so it defaults to True purely for this
# offline collectstatic step - the runtime container reads real env vars).
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Apply migrations, seed the CEFR question bank + writing tasks (both
# commands are idempotent - see apps/assessment and apps/writing management
# commands - so running them on every boot is safe), then start gunicorn.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py import_questions && python manage.py import_writing_tasks && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3"]
