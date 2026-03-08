"""Tests for authentication endpoints."""
import pytest
from fastapi import status


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "role": "parent",
            "phone": "+1234567890",
            "email": "newuser@test.com",
            "password": "SecurePassword123!"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_success(client, test_parent_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_or_email": "parent@test.com",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_or_email": "nonexistent@test.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_duplicate_email(client, test_parent_user):
    """Test registration with duplicate email."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "role": "parent",
            "phone": "+9999999999",
            "email": "parent@test.com",  # Already exists
            "password": "SecurePassword123!"
        }
    )
    assert response.status_code == status.HTTP_409_CONFLICT
