"""Full Milestone 3 happy-path integration coverage."""
try:
    from . import _bootstrap  # noqa: F401
except ImportError:  # pragma: no cover - direct script execution fallback
    import _bootstrap  # type: ignore  # noqa: F401

from fastapi import status


def test_full_milestone3_happy_path_register_login_group_child_staff_flow(client, db_session):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "milestone3-flow@test.com",
            "password": "SecurePassword123!",
            "full_name": "Milestone 3 Tenant",
            "phone": "+998901234777",
        },
    )
    assert register_response.status_code == status.HTTP_201_CREATED
    initial_tokens = register_response.json()
    initial_headers = {"Authorization": f"Bearer {initial_tokens['access_token']}"}

    kindergarten_response = client.post(
        "/api/v1/kindergartens/",
        json={
            "kinder_name": "Milestone 3 Kindergarten",
            "region": "Tashkent",
            "district": "Yunusabad",
            "address": "Integration Street 1",
            "phone": "+998901234778",
            "email": "milestone3-kindergarten@test.com",
            "payment_note": "Monthly",
        },
        headers=initial_headers,
    )
    assert kindergarten_response.status_code == status.HTTP_201_CREATED
    kindergarten = kindergarten_response.json()

    from app.models.kindergarten import Kindergarten

    kindergarten_model = db_session.query(Kindergarten).filter(
        Kindergarten.kindergarten_id == kindergarten["kindergarten_id"]
    ).one()
    kindergarten_model.is_verified = True
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "milestone3-flow@test.com", "password": "SecurePassword123!"},
    )
    assert login_response.status_code == status.HTTP_200_OK
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    group_response = client.post(
        "/api/v1/groups/",
        json={
            "name": "Integration Group",
            "age_from": 3,
            "age_to": 6,
            "capacity": 18,
            "schedule_from": "08:30:00",
            "schedule_to": "17:30:00",
            "monthly_fee": "650000",
        },
        headers=headers,
    )
    assert group_response.status_code == status.HTTP_201_CREATED
    group = group_response.json()

    child_response = client.post(
        "/api/v1/children/",
        json={
            "full_name": "Integration Child",
            "birth_date": "2021-04-12",
            "gender": "female",
            "parent_phone": "+998901234779",
            "group_id": group["group_id"],
            "notes": "Happy path child",
        },
        headers=headers,
    )
    assert child_response.status_code == status.HTTP_201_CREATED
    child = child_response.json()

    staff_response = client.post(
        "/api/v1/staff/",
        json={
            "full_name": "Integration Pedagogue",
            "phone": "+998901234780",
            "role": "teacher",
            "salary": "4200000",
            "hired_at": "2025-09-01",
            "group_id": group["group_id"],
        },
        headers=headers,
    )
    assert staff_response.status_code == status.HTTP_201_CREATED
    staff_member = staff_response.json()

    refreshed_group_response = client.get(f"/api/v1/groups/{group['group_id']}", headers=headers)
    assert refreshed_group_response.status_code == status.HTTP_200_OK
    refreshed_group = refreshed_group_response.json()

    assert kindergarten["kindergarten_id"] == group["kindergarten_id"]
    assert group["kindergarten_id"] == child["kindergarten_id"]
    assert child["kindergarten_id"] == staff_member["kindergarten_id"]
    assert child["group_id"] == group["group_id"]
    assert staff_member["group_id"] == group["group_id"]
    assert refreshed_group["teacher_id"] == staff_member["teacher_id"]


def test_group_staff_assignment_is_supported_via_staff_group_id(
    client, verified_tenant, create_group, create_staff
):
    group = create_group(verified_tenant)
    staff_member = create_staff(verified_tenant, group_id=group["group_id"])

    group_response = client.get(f"/api/v1/groups/{group['group_id']}", headers=verified_tenant["headers"])

    assert group_response.status_code == status.HTTP_200_OK
    assert group_response.json()["teacher_id"] == staff_member["teacher_id"]
