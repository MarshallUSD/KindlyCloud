"""Tests for kindergarten endpoints."""
import pytest
from fastapi import status

PENDING_VERIFICATION_DETAIL = "Kindergarten account is pending verification"


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
            "name": "Rainbow Group",
            "age_from": 3,
            "age_to": 5,
            "capacity": 20,
            "schedule_from": "08:00:00",
            "schedule_to": "18:00:00",
            "monthly_fee": "500000",
            "teacher_id": test_pedagogue.teacher_id,
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Rainbow Group"


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


def test_create_child(client, test_kindergarten_user_token, test_kindergarten, test_group):
    """Test creating a child."""
    response = client.post(
        "/api/v1/kindergartens/children",
        json={
            "full_name": "Ali Karimov",
            "birth_date": "2021-05-15",
            "parent_phone": "+998901234567",
            "group_id": test_group.group_id,
            "gender": "male",
            "address": "456 Park Avenue"
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["full_name"] == "Ali Karimov"


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
    # HTTPBearer returns 403 when credentials are missing
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unverified_kindergarten_can_access_auth_me(
    client, test_kindergarten_user_token, test_unverified_kindergarten
):
    """Unverified kindergarten users can still inspect their own auth payload."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["role"] == "kindergarten"
    assert data["kindergarten_id"] == test_unverified_kindergarten.kindergarten_id


def test_unverified_kindergarten_can_access_kindergarten_me(
    client, test_kindergarten_user_token, test_unverified_kindergarten
):
    """Unverified kindergarten users can still access their own profile."""
    response = client.get(
        "/api/v1/kindergartens/me",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["kindergarten_id"] == test_unverified_kindergarten.kindergarten_id
    assert data["is_verified"] is False


@pytest.mark.parametrize(
    ("method", "path", "payload", "fixture_names"),
    [
        ("get", "/api/v1/kindergartens/groups", None, ("test_unverified_kindergarten",)),
        (
            "post",
                "/api/v1/kindergartens/groups",
            {
                "name": "Pending Group",
                "age_from": 3,
                "age_to": 5,
                "capacity": 20,
                "schedule_from": "08:00:00",
                "schedule_to": "18:00:00",
                "monthly_fee": "500000",
                "teacher_id": "{teacher_id}",
            },
            ("test_unverified_kindergarten", "test_pedagogue"),
        ),
        (
            "post",
            "/api/v1/kindergartens/children",
            {
                "full_name": "Ali Karimov",
                "birth_date": "2021-05-15",
                "parent_phone": "+998901234567",
                "group_id": "{group_id}",
                "gender": "male",
                "address": "456 Park Avenue",
            },
            ("test_unverified_kindergarten", "test_group"),
        ),
        (
            "post",
            "/api/v1/kindergartens/enrollments",
            {
                "child_id": "{child_id}",
                "group_id": "{group_id}",
                "enrol_date": "2026-03-10",
                "total_fees": "500000",
            },
            ("test_unverified_kindergarten", "test_child", "test_group"),
        ),
        (
            "post",
            "/api/v1/kindergartens/attendance",
            {
                "enrol_id": "{enrol_id}",
                "attend_date": "2026-03-10",
                "status": "present",
                "notes": "On time",
            },
            ("test_unverified_kindergarten", "test_enrollment"),
        ),
        (
            "post",
            "/api/v1/kindergartens/menus",
            {
                "menu_date": "2026-03-10",
                "items": [
                    {
                        "meal": "breakfast",
                        "title": "Oatmeal",
                        "description": "Warm oatmeal",
                        "calories": 250,
                    }
                ],
            },
            ("test_unverified_kindergarten",),
        ),
    ],
)
def test_unverified_kindergarten_cannot_access_operational_endpoints(
    client,
    test_kindergarten_user_token,
    request,
    method,
    path,
    payload,
    fixture_names,
):
    """Unverified kindergarten users are blocked from operational routes."""
    context = {name: request.getfixturevalue(name) for name in fixture_names}
    body = payload
    if isinstance(payload, dict):
        rendered = {}
        for key, value in payload.items():
            if isinstance(value, list):
                rendered[key] = [
                    {
                        nested_key: nested_value.format(**{
                            "teacher_id": getattr(context.get("test_pedagogue"), "teacher_id", ""),
                            "child_id": getattr(context.get("test_child"), "child_id", ""),
                            "group_id": getattr(context.get("test_group"), "group_id", ""),
                            "enrol_id": getattr(context.get("test_enrollment"), "enrol_id", ""),
                        }) if isinstance(nested_value, str) else nested_value
                        for nested_key, nested_value in item.items()
                    }
                    for item in value
                ]
            elif isinstance(value, str):
                rendered[key] = value.format(**{
                    "teacher_id": getattr(context.get("test_pedagogue"), "teacher_id", ""),
                    "child_id": getattr(context.get("test_child"), "child_id", ""),
                    "group_id": getattr(context.get("test_group"), "group_id", ""),
                    "enrol_id": getattr(context.get("test_enrollment"), "enrol_id", ""),
                })
            else:
                rendered[key] = value
        body = rendered

    request_kwargs = {
        "headers": {"Authorization": f"Bearer {test_kindergarten_user_token}"},
    }
    if body is not None:
        request_kwargs["json"] = body

    response = getattr(client, method)(path, **request_kwargs)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == PENDING_VERIFICATION_DETAIL


def test_verified_kindergarten_can_access_operational_endpoint(client, test_kindergarten_user_token, test_group):
    """Verified kindergarten users keep normal access."""
    response = client.get(
        "/api/v1/kindergartens/groups",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
