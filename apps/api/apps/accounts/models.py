from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for LingoLab.

    We extend Django's built-in user from the start (instead of using
    ``django.contrib.auth.models.User`` directly) so that future sprints
    can add platform-specific fields (CEFR profile, role, etc.) without a
    disruptive migration to a custom user model later.
    """

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        # NOTE (Sprint 3 scope decision): TEACHER exists as a selectable
        # value and is exposed in serializers, but no teacher-specific
        # permission class or endpoint exists yet - only the two-tier
        # IsAdmin / regular-user scheme is implemented. Deliberately kept
        # out of scope for Sprint 3 (tracked as a "nice to have", not a
        # blocker); a real teacher role is a Sprint 4+ feature.
        TEACHER = "teacher", "Teacher"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text="Drives access to admin-only endpoints (question bank CRUD, user management).",
    )
    is_guest = models.BooleanField(
        default=False,
        help_text=(
            "True for accounts created via the 'Continue as Guest' flow: no "
            "email/password, temporary access so a learner can try the "
            "platform before deciding to create a full account."
        ),
    )

    def save(self, *args, **kwargs):
        # Keep `role` consistent with Django's own superuser flag, so
        # `createsuperuser` is enough to get admin API access - no extra
        # manual step required.
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
