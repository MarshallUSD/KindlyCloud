"""Milestone 1 authentication and token integration tests."""
try:
    from . import _bootstrap  # noqa: F401
except ImportError:  # pragma: no cover - direct script execution fallback
    import _bootstrap  # type: ignore  # noqa: F401

from fastapi import status

from app.core.security import decode_token


def test_successful_kindergarten_registration(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "fresh-kindergarten@test.com",
            "password": "SecurePassword123!",
            "full_name": "Fresh Kindergarten",
            "phone": "+998901234001",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


def test_duplicate_registration_rejected(client):
    payload = {
        "email": "duplicate-kindergarten@test.com",
        "password": "SecurePassword123!",
        "full_name": "Duplicate Kindergarten",
        "phone": "+998901234002",
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_409_CONFLICT
    assert second_response.json()["detail"] == "User with this email or phone already exists"


def test_successful_login_returns_access_and_refresh_tokens(client, tenant_factory):
    tenant = tenant_factory(email="login-success@test.com", create_kindergarten=False)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": tenant["email"], "password": tenant["password"]},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_invalid_password_rejected(client, tenant_factory):
    tenant = tenant_factory(email="wrong-password@test.com", create_kindergarten=False)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": tenant["email"], "password": "WrongPassword123!"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid credentials"


def test_protected_endpoint_without_token_rejected(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_malformed_token_rejected(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer definitely-not-a-jwt"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid or expired token"


def test_access_token_can_be_used_on_protected_endpoint(client, verified_tenant):
    response = client.get("/api/v1/auth/me", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_id"] == str(verified_tenant["user"].user_id)
    assert data["role"] == "kindergarten"
    assert data["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id


def test_token_claims_include_identity_and_role_for_verified_tenant(verified_tenant):
    payload = decode_token(verified_tenant["tokens"]["access_token"])

    assert payload is not None
    assert payload["sub"] == str(verified_tenant["user"].user_id)
    assert payload["role"] == "kindergarten"
    assert payload["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id
    assert payload["type"] == "access"


def test_role_restriction_blocks_parent_from_kindergarten_only_route(client, parent_account):
    response = client.get("/api/v1/groups/", headers=parent_account["headers"])

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Kindergarten role required"


def test_role_restriction_blocks_kindergarten_from_admin_route(client, verified_tenant):
    response = client.get("/api/v1/admin/feedback", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Admin privileges required"
