"""Tests for parent endpoints."""
import pytest
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
        headers={"Authorization": f"Bearer {test_parent_user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1


def test_create_payment(client, test_parent_user_token, test_enrollment, test_parent, test_parent_child_link):
    """Test creating a payment."""
    response = client.post(
        "/api/v1/parent/payments",
        json={
            "enrol_id": test_enrollment.enrol_id,
            "amount": "100000.00",
            "payment_date": "2026-03-10",
            "provider": "cash",
            "transaction_id": "TXN123456"
        },
        headers={"Authorization": f"Bearer {test_parent_user_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["amount"] == "100000.00"


def test_list_payments(client, test_parent_user_token, test_parent):
    """Test listing payments."""
    response = client.get(
        "/api/v1/parent/payments",
        headers={"Authorization": f"Bearer {test_parent_user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_unauthorized_parent_access(client):
    """Test accessing parent routes without auth."""
    response = client.get("/api/v1/parent/children")
    # HTTPBearer returns 403 when credentials are missing
    assert response.status_code == status.HTTP_403_FORBIDDEN
