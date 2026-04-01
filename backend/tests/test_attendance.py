"""Attendance endpoint tests."""
from datetime import date

from fastapi import status
from sqlalchemy import func

from app.models.attendance import Attendance


def test_bulk_attendance_save_success(client, verified_tenant, create_group, create_child):
    group = create_group(verified_tenant, name="Attendance Group")
    child_one = create_child(verified_tenant, group["group_id"], full_name="Ali Karimov")
    child_two = create_child(verified_tenant, group["group_id"], full_name="Sara Aliyeva")

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-30",
            "records": [
                {"child_id": child_one["child_id"], "status": "present"},
                {"child_id": child_two["child_id"], "status": "late"},
            ],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["group_id"] == group["group_id"]
    assert data["date"] == "2026-03-30"
    assert {item["child_id"]: item["status"] for item in data["records"]} == {
        child_one["child_id"]: "present",
        child_two["child_id"]: "late",
    }


def test_second_bulk_save_updates_existing_records_instead_of_creating_duplicates(
    client,
    db_session,
    verified_tenant,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Upsert Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Aziz Rahimov")

    first_response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-30",
            "records": [{"child_id": child["child_id"], "status": "absent"}],
        },
        headers=verified_tenant["headers"],
    )
    assert first_response.status_code == status.HTTP_200_OK, first_response.text

    second_response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-30",
            "records": [{"child_id": child["child_id"], "status": "present"}],
        },
        headers=verified_tenant["headers"],
    )
    assert second_response.status_code == status.HTTP_200_OK, second_response.text

    total_records = db_session.query(func.count(Attendance.attendance_id)).scalar()
    assert total_records == 1

    record = db_session.query(Attendance).one()
    assert record.child_id == child["child_id"]
    assert record.status == "present"
    assert record.attend_date == date(2026, 3, 30)


def test_daily_endpoint_returns_all_group_children_even_when_not_marked(
    client,
    verified_tenant,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Daily Group")
    child_one = create_child(verified_tenant, group["group_id"], full_name="Ali Karimov")
    child_two = create_child(verified_tenant, group["group_id"], full_name="Sara Aliyeva")

    response = client.get(
        f"/api/v1/attendance/daily?group_id={group['group_id']}&date=2026-03-30",
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["group_id"] == group["group_id"]
    assert {item["child_id"] for item in data["items"]} == {child_one["child_id"], child_two["child_id"]}
    assert all(item["status"] is None for item in data["items"])


def test_history_endpoint_filters_correctly(client, verified_tenant, create_group, create_child):
    group = create_group(verified_tenant, name="History Group")
    other_group = create_group(verified_tenant, name="Other Group")
    child_one = create_child(verified_tenant, group["group_id"], full_name="Ali Karimov")
    child_two = create_child(verified_tenant, other_group["group_id"], full_name="Sara Aliyeva")

    client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-10",
            "records": [{"child_id": child_one["child_id"], "status": "present"}],
        },
        headers=verified_tenant["headers"],
    )
    client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-15",
            "records": [{"child_id": child_one["child_id"], "status": "late"}],
        },
        headers=verified_tenant["headers"],
    )
    client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": other_group["group_id"],
            "date": "2026-03-15",
            "records": [{"child_id": child_two["child_id"], "status": "absent"}],
        },
        headers=verified_tenant["headers"],
    )

    response = client.get(
        f"/api/v1/attendance/history?group_id={group['group_id']}&date_from=2026-03-11&date_to=2026-03-30",
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["child_id"] == child_one["child_id"]
    assert data[0]["status"] == "late"
    assert data[0]["date"] == "2026-03-15"


def test_summary_counts_are_correct(client, verified_tenant, create_group, create_child):
    group = create_group(verified_tenant, name="Summary Group")
    child_one = create_child(verified_tenant, group["group_id"], full_name="Ali Karimov")
    child_two = create_child(verified_tenant, group["group_id"], full_name="Sara Aliyeva")
    child_three = create_child(verified_tenant, group["group_id"], full_name="Aziza Saidova")
    create_child(verified_tenant, group["group_id"], full_name="Bekzod Karimov")

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-30",
            "records": [
                {"child_id": child_one["child_id"], "status": "present"},
                {"child_id": child_two["child_id"], "status": "late"},
                {"child_id": child_three["child_id"], "status": "absent"},
            ],
        },
        headers=verified_tenant["headers"],
    )
    assert response.status_code == status.HTTP_200_OK, response.text

    summary_response = client.get(
        f"/api/v1/attendance/summary?group_id={group['group_id']}&date=2026-03-30",
        headers=verified_tenant["headers"],
    )

    assert summary_response.status_code == status.HTTP_200_OK, summary_response.text
    data = summary_response.json()
    assert data == {
        "group_id": group["group_id"],
        "date": "2026-03-30",
        "total_children": 4,
        "present_count": 1,
        "late_count": 1,
        "absent_count": 1,
        "unmarked_count": 1,
    }


def test_invalid_status_is_rejected(client, verified_tenant, create_group, create_child):
    group = create_group(verified_tenant, name="Invalid Status Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Ali Karimov")

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-30",
            "records": [{"child_id": child["child_id"], "status": "excused"}],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_child_from_another_group_is_rejected(client, verified_tenant, create_group, create_child):
    group = create_group(verified_tenant, name="Main Group")
    other_group = create_group(verified_tenant, name="Different Group")
    child = create_child(verified_tenant, other_group["group_id"], full_name="Ali Karimov")

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-30",
            "records": [{"child_id": child["child_id"], "status": "present"}],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Child does not belong to the selected group"


def test_child_from_another_tenant_is_rejected(
    client,
    verified_tenant,
    second_verified_tenant,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Tenant One Group")
    foreign_group = create_group(second_verified_tenant, name="Tenant Two Group")
    foreign_child = create_child(second_verified_tenant, foreign_group["group_id"], full_name="Foreign Child")

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-30",
            "records": [{"child_id": foreign_child["child_id"], "status": "present"}],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "You cannot access another kindergarten's child"


def test_unauthorized_roles_cannot_access_attendance_endpoints(
    client,
    parent_account,
    verified_tenant,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Restricted Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Ali Karimov")

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-30",
            "records": [{"child_id": child["child_id"], "status": "present"}],
        },
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Kindergarten role required"


def test_kindergarten_user_can_only_manage_own_tenant_data(
    client,
    verified_tenant,
    second_verified_tenant,
    create_group,
):
    foreign_group = create_group(second_verified_tenant, name="Foreign Group")

    response = client.get(
        f"/api/v1/attendance/daily?group_id={foreign_group['group_id']}&date=2026-03-30",
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "You cannot use a group from another kindergarten"
