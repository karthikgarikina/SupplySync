from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from core import constants
from core.exceptions import DuplicateResourceException, InvalidOperationException


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }


def register_user(data: dict) -> dict:
    """Create a user and return the required registration token payload."""
    if User.all_objects.filter(email=data["email"]).exists():
        raise DuplicateResourceException("Email already exists.", code=constants.ERROR_DUPLICATE_RESOURCE)
    if User.all_objects.filter(username=data["username"]).exists():
        raise DuplicateResourceException("Username already exists.", code=constants.ERROR_DUPLICATE_RESOURCE)
    user = User.objects.create_user(
        email=data["email"],
        password=data["password"],
        username=data["username"],
        full_name=data["full_name"],
        role=data["role"],
    )
    tokens = _tokens_for_user(user)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        **tokens,
    }


def login_user(email: str, password: str) -> dict:
    """Authenticate a user, update last_login_at, and return JWT credentials."""
    user = authenticate(username=email, password=password)
    if user is None:
        raise AuthenticationFailed("Invalid email or password.")
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at", "updated_at"])
    tokens = _tokens_for_user(user)
    return {
        **tokens,
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    }


def change_password(user: User, old_password: str, new_password: str) -> None:
    """Validate the old password and replace it with a new hashed password."""
    if not user.check_password(old_password):
        raise InvalidOperationException("Old password is incorrect.", code=constants.ERROR_INVALID_OPERATION)
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])


def blacklist_refresh_token(refresh_token: str) -> None:
    """Blacklist a refresh token through Simple JWT."""
    token = RefreshToken(refresh_token)
    token.blacklist()

