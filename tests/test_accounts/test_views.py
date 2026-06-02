import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db


def test_register_returns_201_with_valid_request(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "username": "newstaff",
            "email": "newstaff@supplysync.local",
            "password": "Password1!",
            "full_name": "New Staff",
            "role": "STAFF",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert "refresh_token" in response.data


def test_register_returns_409_when_email_already_exists(api_client, admin_user):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "username": "another-admin",
            "email": admin_user.email,
            "password": "Password1!",
            "full_name": "Another Admin",
            "role": "ADMIN",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_login_returns_200_with_valid_credentials(api_client, staff_user):
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": staff_user.email, "password": "Password1!"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data


def test_login_returns_401_with_invalid_credentials(api_client, staff_user):
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": staff_user.email, "password": "WrongPassword1!"},
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_token_returns_200_with_valid_refresh_token(api_client, staff_user):
    refresh = RefreshToken.for_user(staff_user)
    response = api_client.post(
        "/api/v1/auth/token/refresh/",
        {"refresh": str(refresh)},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
