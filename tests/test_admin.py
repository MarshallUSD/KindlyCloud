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
