"""Tests for admin endpoints."""
import pytest
from fastapi import status


def test_create_admin_post(client, test_admin_token, test_kindergarten):
    """Test creating an admin post."""
    response = client.post(
        "/api/v1/admin/posts",
        json={
            "title": "Important Announcement",
            "body": "This is an important announcement for all kindergartens.",
            "target_kindergarten_id": test_kindergarten.kindergarten_id
        },
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Important Announcement"
    assert "post_id" in data


def test_non_admin_cannot_create_post(client, test_parent_user_token):
    """Test that non-admin users cannot create admin posts."""
    response = client.post(
        "/api/v1/admin/posts",
        json={
            "title": "Test Post",
            "body": "This should fail"
        },
        headers={"Authorization": f"Bearer {test_parent_user_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_feedback_as_admin(client, test_admin_token):
    """Test listing feedback as admin."""
    response = client.get(
        "/api/v1/admin/feedback",
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_admin_verification_changes_access_correctly(
    client, test_admin_token, test_kindergarten_user, test_kindergarten_user_token, test_unverified_kindergarten
):
    """Admin verification flips operational access for the kindergarten user."""
    before_response = client.get(
        "/api/v1/kindergartens/groups",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert before_response.status_code == status.HTTP_403_FORBIDDEN
    assert before_response.json()["detail"] == "Kindergarten account is pending verification"

    verify_response = client.post(
        f"/api/v1/admin/verify-kindergarten/{test_kindergarten_user.user_id}",
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    assert verify_response.status_code == status.HTTP_200_OK
    assert verify_response.json()["message"] == "Kindergarten verified"

    after_response = client.get(
        "/api/v1/kindergartens/groups",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert after_response.status_code == status.HTTP_200_OK
