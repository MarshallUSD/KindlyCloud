"""Tests for parent endpoints."""
from fastapi import status


def test_parent_cannot_self_link_child(client, test_parent_user_token, test_child):
    """Parent self-link endpoint must not exist publicly."""
    response = client.post(
        "/api/v1/parent/link-child",
        json={"child_id": test_child.child_id, "note": "My son"},
        headers={"Authorization": f"Bearer {test_parent_user_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_my_children(client, test_parent_user_token, test_parent_child_link):
    """Test getting my children."""
    response = client.get(
        "/api/v1/parent/children",
        headers={"Authorization": f"Bearer {test_parent_user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1


def test_parent_payment_creation_endpoint_removed(client, test_parent_user_token):
    """Parents are read-only for payment records in milestone 5."""
    response = client.post(
        "/api/v1/parent/payments",
        json={"child_id": "x", "amount": "100000.00", "due_date": "2026-04-10", "billing_period": "2026-04"},
        headers={"Authorization": f"Bearer {test_parent_user_token}"},
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_unauthorized_parent_access(client):
    """Test accessing parent routes without auth."""
    response = client.get("/api/v1/parent/children")
    assert response.status_code == status.HTTP_403_FORBIDDEN
