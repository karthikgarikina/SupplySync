from rest_framework import serializers

from apps.accounts.models import UserRole
from apps.accounts.validators import validate_password_strength


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, allow_blank=False, max_length=50)
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False, write_only=True)
    full_name = serializers.CharField(required=True, allow_blank=False, max_length=150)
    role = serializers.ChoiceField(required=True, choices=UserRole.choices)

    def validate_password(self, value):
        return validate_password_strength(value)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False, write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True, allow_blank=False)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, allow_blank=False, write_only=True)
    new_password = serializers.CharField(required=True, allow_blank=False, write_only=True)

    def validate_new_password(self, value):
        return validate_password_strength(value)

