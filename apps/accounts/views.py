from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts import services
from apps.accounts.serializers import ChangePasswordSerializer, LoginSerializer, LogoutSerializer, RegisterSerializer
from core.throttles import LoginRateLimitThrottle


class RegisterView(APIView):
    """Create a new SupplySync user account and return JWT tokens."""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(request=RegisterSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = services.register_user(serializer.validated_data)
        return Response(payload, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate a user and return JWT tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateLimitThrottle]
    serializer_class = LoginSerializer

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        throttle = LoginRateLimitThrottle()
        try:
            payload = services.login_user(**serializer.validated_data)
        except Exception:
            throttle.register_failure(request)
            raise
        throttle.clear(request)
        return Response(payload, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Blacklist a refresh token for the authenticated user."""

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer)
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.blacklist_refresh_token(serializer.validated_data["refresh_token"])
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @extend_schema(request=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_password(
            request.user,
            serializer.validated_data["old_password"],
            serializer.validated_data["new_password"],
        )
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


class RefreshTokenView(TokenRefreshView):
    """Issue a new access token from a valid refresh token."""

    permission_classes = [AllowAny]
