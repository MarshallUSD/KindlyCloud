"""Tests for parent read endpoints."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
import uuid

from fastapi import status

from app.core.time import utcnow
from app.models.child import ParentChildLink
from app.models.notification import Notification
from app.models.parent import ParentUser
from app.models.payment import Payment
from app.models.pedagogue import Pedagogue


def _link_parent_to_child(db_session, *, parent_id: str, child_id: str, note: str = "Parent link") -> None:
    db_session.add(
        ParentChildLink(
            link_id=str(uuid.uuid4()),
            parent_id=parent_id,
            child_id=child_id,
            note=note,
            status="active",
        )
    )
    db_session.commit()


def _create_menu(client, tenant, *, menu_date: str, group_id: str, status_value: str = "published", notes: str | None = None):
    payload = {
        "menu_date": menu_date,
        "group_ids": [group_id],
        "status": status_value,
        "notes": notes,
        "items": [
            {"meal": "breakfast", "title": "Oatmeal", "description": "Warm oatmeal", "calories": 230},
            {"meal": "lunch", "title": "Soup", "description": "Vegetable soup", "calories": 320},
            {"meal": "snack", "title": "Apple slices", "description": None, "calories": 90},
        ],
    }
    return client.post("/api/v1/kindergartens/menus", json=payload, headers=tenant["headers"])


def _create_payment(client, tenant, *, child_id: str, amount="250000.00", due_date="2026-04-10", billing_period="2026-04"):
    return client.post(
        "/api/v1/payments/",
        json={
            "child_id": child_id,
            "amount": amount,
            "due_date": due_date,
            "billing_period": billing_period,
            "status": "pending",
        },
        headers=tenant["headers"],
    )


def _create_notification(db_session, *, user_id: int, notif_type: str, payload: dict | None = None, read_at=None) -> Notification:
    notification = Notification(
        notification_id=str(uuid.uuid4()),
        user_id=str(user_id),
        notif_type=notif_type,
        payload=payload,
        read_at=read_at,
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


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


def test_parent_dashboard_returns_only_linked_children(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Dashboard Group")
    visible_child = create_child(verified_tenant, group["group_id"], full_name="Visible Child")
    create_child(verified_tenant, group["group_id"], full_name="Hidden Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=visible_child["child_id"])

    response = client.get("/api/v1/parent/dashboard", headers=parent_account["headers"])

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert [item["child_id"] for item in data["children"]] == [visible_child["child_id"]]


def test_parent_dashboard_includes_group_pedagogue_attendance_menu_payment_and_unread_count(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Dashboard Full Group")
    child = create_child(
        verified_tenant,
        group["group_id"],
        full_name="Dashboard Child",
        birth_date="2021-06-15",
        gender="female",
    )
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    pedagogue = Pedagogue(
        teacher_id=str(uuid.uuid4()),
        kindergarten_id=verified_tenant["kindergarten"].kindergarten_id,
        group_id=group["group_id"],
        full_name="Nargiza Xasanova",
        phone="+998901111333",
        role="teacher",
    )
    db_session.add(pedagogue)
    db_session.commit()

    attendance_response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": date.today().isoformat(),
            "records": [{"child_id": child["child_id"], "status": "present"}],
        },
        headers=verified_tenant["headers"],
    )
    assert attendance_response.status_code == status.HTTP_200_OK, attendance_response.text

    menu_response = _create_menu(
        client,
        verified_tenant,
        menu_date=date.today().isoformat(),
        group_id=group["group_id"],
        notes="No peanuts",
    )
    assert menu_response.status_code == status.HTTP_201_CREATED, menu_response.text

    payment_response = _create_payment(
        client,
        verified_tenant,
        child_id=child["child_id"],
        amount="275000.00",
        due_date="2026-04-10",
        billing_period="2026-04",
    )
    assert payment_response.status_code == status.HTTP_201_CREATED, payment_response.text
    payment_id = payment_response.json()["payment_id"]

    _create_notification(
        db_session,
        user_id=parent_account["user"].user_id,
        notif_type="announcement",
        payload={"message": "Reminder"},
    )
    _create_notification(
        db_session,
        user_id=parent_account["user"].user_id,
        notif_type="announcement",
        payload={"message": "Seen"},
        read_at=utcnow(),
    )

    response = client.get("/api/v1/parent/dashboard", headers=parent_account["headers"])

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["unread_notifications_count"] == 2
    child_payload = data["children"][0]
    assert child_payload["full_name"] == "Dashboard Child"
    assert child_payload["birth_date"] == "2021-06-15"
    assert child_payload["gender"] == "female"
    assert child_payload["group"]["group_id"] == group["group_id"]
    assert child_payload["group"]["group_name"] == "Dashboard Full Group"
    assert child_payload["pedagogue"]["full_name"] == "Nargiza Xasanova"
    assert child_payload["pedagogue"]["role"] == "teacher"
    assert child_payload["today_attendance_status"] == "present"
    assert child_payload["today_menu"]["menu_date"] == date.today().isoformat()
    assert child_payload["today_menu"]["status"] == "published"
    assert child_payload["latest_payment"] == {
        "payment_id": payment_id,
        "billing_period": "2026-04",
        "amount": "275000.00",
        "status": "pending",
        "due_date": "2026-04-10",
    }


def test_parent_dashboard_returns_unmarked_when_no_attendance_exists(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Unmarked Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Unmarked Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    response = client.get("/api/v1/parent/dashboard", headers=parent_account["headers"])

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["children"][0]["today_attendance_status"] == "unmarked"


def test_parent_attendance_exact_date_query_works(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Attendance Exact Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Attendance Exact Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-03-20",
            "records": [{"child_id": child["child_id"], "status": "late"}],
        },
        headers=verified_tenant["headers"],
    )

    response = client.get(
        f"/api/v1/parent/attendance?child_id={child['child_id']}&date=2026-03-20",
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == [
        {
            "child_id": child["child_id"],
            "child_name": "Attendance Exact Child",
            "group_id": group["group_id"],
            "group_name": "Attendance Exact Group",
            "date": "2026-03-20",
            "status": "late",
        }
    ]


def test_parent_attendance_date_range_query_works(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Attendance Range Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Attendance Range Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    for attend_date, status_value in [("2026-03-10", "present"), ("2026-03-15", "absent"), ("2026-03-22", "late")]:
        client.post(
            "/api/v1/attendance/bulk",
            json={
                "group_id": group["group_id"],
                "date": attend_date,
                "records": [{"child_id": child["child_id"], "status": status_value}],
            },
            headers=verified_tenant["headers"],
        )

    response = client.get(
        f"/api/v1/parent/attendance?child_id={child['child_id']}&date_from=2026-03-11&date_to=2026-03-22",
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert [item["date"] for item in response.json()] == ["2026-03-22", "2026-03-15"]


def test_parent_attendance_blocks_access_to_unrelated_child_id_with_403(
    client,
    verified_tenant,
    parent_account,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Attendance Block Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Not Linked Child")

    response = client.get(
        f"/api/v1/parent/attendance?child_id={child['child_id']}&date=2026-03-20",
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Child is not linked to this parent"


def test_parent_menu_returns_correct_group_menu_for_linked_child(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Menu Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Menu Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    menu_response = _create_menu(client, verified_tenant, menu_date="2026-04-01", group_id=group["group_id"])
    assert menu_response.status_code == status.HTTP_201_CREATED, menu_response.text

    response = client.get(
        f"/api/v1/parent/menu?child_id={child['child_id']}&date=2026-04-01",
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["group_id"] == group["group_id"]
    assert data["group_name"] == "Menu Group"
    assert data["menu_date"] == "2026-04-01"
    assert [item["meal"] for item in data["items"]] == ["breakfast", "lunch", "snack"]


def test_parent_menu_defaults_to_today_when_date_is_omitted(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Menu Today Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Menu Today Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    _create_menu(client, verified_tenant, menu_date=date.today().isoformat(), group_id=group["group_id"])

    response = client.get(
        f"/api/v1/parent/menu?child_id={child['child_id']}",
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["menu_date"] == date.today().isoformat()


def test_parent_menu_hides_draft_menu_from_parent(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Draft Menu Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Draft Menu Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    draft_response = _create_menu(
        client,
        verified_tenant,
        menu_date="2026-04-02",
        group_id=group["group_id"],
        status_value="draft",
    )
    assert draft_response.status_code == status.HTTP_201_CREATED, draft_response.text

    response = client.get(
        f"/api/v1/parent/menu?child_id={child['child_id']}&date=2026-04-02",
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Published menu not found"


def test_parent_menu_returns_not_found_when_no_published_menu_exists(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="No Menu Group")
    child = create_child(verified_tenant, group["group_id"], full_name="No Menu Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    response = client.get(
        f"/api/v1/parent/menu?child_id={child['child_id']}&date=2026-04-03",
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Published menu not found"


def test_parent_notifications_list_returns_only_current_parent_notifications(
    client,
    parent_account,
    parent_factory,
    db_session,
):
    other_parent = parent_factory()
    _create_notification(db_session, user_id=parent_account["user"].user_id, notif_type="payment_created", payload={"x": 1})
    _create_notification(db_session, user_id=parent_account["user"].user_id, notif_type="payment_overdue", payload={"x": 2})
    _create_notification(db_session, user_id=other_parent["user"].user_id, notif_type="payment_created", payload={"x": 3})

    response = client.get("/api/v1/parent/notifications", headers=parent_account["headers"])

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["total"] == 2
    assert {item["notif_type"] for item in data["items"]} == {"payment_created", "payment_overdue"}
    assert all(item["user_id"] == str(parent_account["user"].user_id) for item in data["items"])


def test_parent_mark_notification_as_read_works_only_for_own_notification(
    client,
    parent_account,
    parent_factory,
    db_session,
):
    other_parent = parent_factory()
    own_notification = _create_notification(
        db_session,
        user_id=parent_account["user"].user_id,
        notif_type="announcement",
        payload={"message": "Unread"},
    )
    foreign_notification = _create_notification(
        db_session,
        user_id=other_parent["user"].user_id,
        notif_type="announcement",
        payload={"message": "Foreign"},
    )

    own_response = client.patch(
        f"/api/v1/parent/notifications/{own_notification.notification_id}/read",
        headers=parent_account["headers"],
    )
    foreign_response = client.patch(
        f"/api/v1/parent/notifications/{foreign_notification.notification_id}/read",
        headers=parent_account["headers"],
    )

    assert own_response.status_code == status.HTTP_200_OK, own_response.text
    assert own_response.json()["is_read"] is True
    assert own_response.json()["read_at"] is not None
    assert foreign_response.status_code == status.HTTP_403_FORBIDDEN
    assert foreign_response.json()["detail"] == "You do not have access to this notification"


def test_parent_legacy_menus_today_route_is_preserved(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Legacy Menu Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Legacy Menu Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    _create_menu(client, verified_tenant, menu_date=date.today().isoformat(), group_id=group["group_id"])

    response = client.get(
        f"/api/v1/parent/menus/today?child_id={child['child_id']}",
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["menu_date"] == date.today().isoformat()
    assert data["status"] == "published"
    assert len(data["items"]) == 3


def test_menu_uniqueness_per_group_date_is_enforced(
    client,
    verified_tenant,
    create_group,
):
    group = create_group(verified_tenant, name="Unique Menu Group")

    first_response = _create_menu(client, verified_tenant, menu_date="2026-04-05", group_id=group["group_id"])
    second_response = _create_menu(client, verified_tenant, menu_date="2026-04-05", group_id=group["group_id"])

    assert first_response.status_code == status.HTTP_201_CREATED, first_response.text
    assert second_response.status_code == status.HTTP_409_CONFLICT
    assert second_response.json()["detail"] == "Menu already exists for this group and date"
