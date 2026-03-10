"""Tests for kindergarten endpoints."""
import pytest
from fastapi import status


def test_create_kindergarten(client, test_kindergarten_user_token):
    """Test creating kindergarten profile."""
    response = client.post(
        "/api/v1/kindergartens/",
        json={
            "kinder_name": "Little Stars Kindergarten",
            "region": "Tashkent",
            "district": "Yunusabad",
            "address": "123 Main Street",
            "phone": "+998901234567",
            "email": "littlestars@test.com",
            "payment_note": "Monthly payment required"
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["kinder_name"] == "Little Stars Kindergarten"
    assert "kindergarten_id" in data


def test_get_my_kindergarten(client, test_kindergarten_user_token, test_kindergarten):
    """Test getting own kindergarten."""
    response = client.get(
        "/api/v1/kindergartens/me",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["kindergarten_id"] == test_kindergarten.kindergarten_id


def test_create_group(client, test_kindergarten_user_token, test_kindergarten, test_pedagogue):
    """Test creating a group."""
    response = client.post(
        "/api/v1/kindergartens/groups",
        json={
            "group_name": "Rainbow Group",
            "teacher_id": test_pedagogue.pedagogue_id,
            "start_date": "2026-03-01",
            "end_date": "2026-12-31",
            "schedule": "Monday-Friday 8:00-18:00",
            "max_capacity": 20
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["group_name"] == "Rainbow Group"


def test_list_groups(client, test_kindergarten_user_token, test_group):
    """Test listing groups."""
    response = client.get(
        "/api/v1/kindergartens/groups",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_create_child(client, test_kindergarten_user_token):
    """Test creating a child."""
    response = client.post(
        "/api/v1/kindergartens/children",
        json={
            "first_name": "Ali",
            "last_name": "Karimov",
            "birth_date": "2021-05-15",
            "gender": "male",
            "address": "456 Park Avenue"
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["first_name"] == "Ali"
    assert data["last_name"] == "Karimov"


def test_create_enrollment(client, test_kindergarten_user_token, test_child, test_group):
    """Test creating an enrollment."""
    response = client.post(
        "/api/v1/kindergartens/enrollments",
        json={
            "child_id": test_child.child_id,
            "group_id": test_group.group_id,
            "enrol_date": "2026-03-10",
            "total_fees": "500000"
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["child_id"] == test_child.child_id
    assert data["group_id"] == test_group.group_id


def test_unauthorized_access(client):
    """Test accessing kindergarten routes without auth."""
    response = client.get("/api/v1/kindergartens/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
