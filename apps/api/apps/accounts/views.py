from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
import uuid

from apps.common.pagination import StandardResultsSetPagination

from .permissions import IsAdmin
from .serializers import (
    AdminUserSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    SignUpSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema(
    summary="Register a new user",
    description="Creates a new LingoLab account and returns an auth token.",
    request=SignUpSerializer,
)
class SignUpView(generics.CreateAPIView):
    """POST /api/v1/auth/signup/"""

    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = "auth-signup"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    summary="Log in",
    description="Authenticates a user by username/password and returns an auth token.",
    request=LoginSerializer,
)
class LoginView(APIView):
    """POST /api/v1/auth/login/"""

    permission_classes = (permissions.AllowAny,)
    throttle_scope = "auth-login"

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="Get, update, or delete the current authenticated user",
    description=(
        "Returns 401 if no/invalid auth token is supplied. PATCH returns "
        "400 on validation errors (e.g. invalid email). DELETE is "
        "irreversible and returns 204 on success."
    ),
)
class MeView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/auth/me/ - view your own profile.
    PATCH /api/v1/auth/me/ - update first_name / last_name / email.
    DELETE /api/v1/auth/me/ - permanently delete your own account.
    """

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return ProfileUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        # Return the full, up-to-date UserSerializer representation after a
        # PATCH, not just the (narrower) ProfileUpdateSerializer fields.
        super().update(request, *args, **kwargs)
        return Response(UserSerializer(request.user).data)


@extend_schema(
    summary="Continue as guest",
    description=(
        "Creates a temporary, password-less guest account and returns an "
        "auth token immediately - no form to fill in. Lets a learner try "
        "the placement test before deciding to register. Guest accounts "
        "can be upgraded to a full account later (not yet implemented in "
        "Sprint 1)."
    ),
)
class GuestLoginView(APIView):
    """POST /api/v1/auth/guest/"""

    permission_classes = (permissions.AllowAny,)
    throttle_scope = "auth-guest"

    def post(self, request, *args, **kwargs):
        username = f"guest_{uuid.uuid4().hex[:10]}"
        user = User(username=username, is_guest=True)
        user.set_unusable_password()
        user.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    summary="List all users (admin only)",
    description="Paginated. Returns 403 for any non-admin caller.",
)
class AdminUserListView(generics.ListAPIView):
    """GET /api/v1/auth/users/"""

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = AdminUserSerializer
    permission_classes = (IsAdmin,)
    pagination_class = StandardResultsSetPagination


@extend_schema(
    summary="Retrieve / update / delete any user (admin only)",
    description="Returns 403 for any non-admin caller, 404 if the user id doesn't exist.",
)
class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/auth/users/{id}/"""

    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = (IsAdmin,)
