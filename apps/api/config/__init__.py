# Makes sure the Celery app is always loaded when Django starts, so that
# `@shared_task` (used in apps/writing/tasks.py) works out of the box.
from .celery import app as celery_app

__all__ = ("celery_app",)
