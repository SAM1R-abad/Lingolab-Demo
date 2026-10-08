from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Grants access only to users with role == User.Role.ADMIN (which is kept
    in sync with Django's is_superuser flag - see accounts.models.User.save).
    Used to gate content-management endpoints (question bank CRUD, user
    management) added in Sprint 2.
    """

    message = "This action requires an admin account."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "admin"
        )
