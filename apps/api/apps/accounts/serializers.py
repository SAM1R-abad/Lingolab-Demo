from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    """
    Registration serializer.

    Sprint 1 note: this is intentionally a simple structure (no email
    verification, no captcha, no rate limiting) as agreed for the MVP.
    Passwords are still stored using Django's standard password hashing.
    """

    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6, label="Confirm password")

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account is disabled.")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "is_guest")


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH /api/v1/auth/me/ - a user editing their own profile. Deliberately
    excludes `username`, `password`, and `role`: identity/credentials and
    permissions are not self-service in Sprint 2.
    """

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        extra_kwargs = {field: {"required": False} for field in ("first_name", "last_name", "email")}


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Admin-only user management (list/detail/update/delete). Lets an admin
    change a user's role or deactivate an account, but never exposes or
    accepts a password here.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_guest",
            "is_active",
            "date_joined",
        )
        read_only_fields = ("id", "username", "is_guest", "date_joined")
