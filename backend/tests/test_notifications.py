"""Structured notification and announcement tests."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import status

from config import settings
from app.models.child import ParentChildLink
from app.models.notification import (
    Announcement,
    Notification,
    NotificationDeliveryStats,
    NotificationEventType,
    NotificationType,
    ParentNotificationSettings,
    TelegramDeliveryStatus,
)


def _link_parent_to_child(db_session, *, parent_id: str, child_id: str) -> None:
    db_session.add(
        ParentChildLink(
            link_id=str(uuid.uuid4()),
            parent_id=parent_id,
            child_id=child_id,
            status="active",
        )
    )
    db_session.commit()


def _create_payment(client, tenant, *, child_id: str, billing_period="2026-04", due_date=None):
    response = client.post(
        "/api/v1/payments/",
        json={
            "child_id": child_id,
            "amount": "250000.00",
            "due_date": due_date or (date.today() + timedelta(days=5)).isoformat(),
            "billing_period": billing_period,
            "status": "pending",
        },
        headers=tenant["headers"],
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def test_attendance_late_creates_notification(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Late Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Late Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-04-02",
            "records": [{"child_id": child["child_id"], "status": "late"}],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    notifications = db_session.query(Notification).all()
    assert len(notifications) == 1
    assert notifications[0].type == NotificationType.SYSTEM
    assert notifications[0].event_type == NotificationEventType.ATTENDANCE_LATE


def test_attendance_absent_creates_notification(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Absent Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Absent Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-04-03",
            "records": [{"child_id": child["child_id"], "status": "absent"}],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    notifications = db_session.query(Notification).all()
    assert len(notifications) == 1
    assert notifications[0].event_type == NotificationEventType.ATTENDANCE_ABSENT


def test_duplicate_attendance_event_same_child_date_does_not_duplicate_notification(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Dedup Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Dedup Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    for _ in range(2):
        response = client.post(
            "/api/v1/attendance/bulk",
            json={
                "group_id": group["group_id"],
                "date": "2026-04-04",
                "records": [{"child_id": child["child_id"], "status": "late"}],
            },
            headers=verified_tenant["headers"],
        )
        assert response.status_code == status.HTTP_200_OK, response.text

    notifications = (
        db_session.query(Notification)
        .filter(Notification.event_type == NotificationEventType.ATTENDANCE_LATE)
        .all()
    )
    assert len(notifications) == 1


def test_payment_created_notification_is_created_correctly(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Payment Created Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Payment Created Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    payment = _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-04")

    notification = db_session.query(Notification).filter(Notification.child_id == child["child_id"]).one()
    assert notification.event_type == NotificationEventType.PAYMENT_CREATED
    assert notification.dedup_key == f"payment_created:{payment['payment_id']}:{parent_account['parent'].parent_id}"


def test_payment_overdue_notification_is_created_correctly(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Payment Overdue Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Payment Overdue Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    payment = _create_payment(
        client,
        verified_tenant,
        child_id=child["child_id"],
        billing_period="2026-01",
        due_date=(date.today() - timedelta(days=2)).isoformat(),
    )

    response = client.get(f"/api/v1/payments/{payment['payment_id']}", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_200_OK, response.text
    overdue = (
        db_session.query(Notification)
        .filter(Notification.event_type == NotificationEventType.PAYMENT_OVERDUE)
        .one()
    )
    assert overdue.dedup_key == f"payment_overdue:{payment['payment_id']}:{parent_account['parent'].parent_id}"


def test_payment_paid_notification_is_created_correctly(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Payment Paid Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Payment Paid Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    payment = _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-05")

    response = client.patch(
        f"/api/v1/payments/{payment['payment_id']}/mark-paid",
        json={"payment_method": "cash"},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    paid = (
        db_session.query(Notification)
        .filter(Notification.event_type == NotificationEventType.PAYMENT_PAID)
        .one()
    )
    assert paid.dedup_key == f"payment_paid:{payment['payment_id']}:{parent_account['parent'].parent_id}"


def test_kindergarten_can_create_announcement_for_all_parents(
    client,
    verified_tenant,
    parent_account,
    parent_factory,
    db_session,
    create_group,
    create_child,
):
    other_parent = parent_factory()
    group = create_group(verified_tenant, name="All Announcement Group")
    child_a = create_child(verified_tenant, group["group_id"], full_name="All Child A")
    child_b = create_child(verified_tenant, group["group_id"], full_name="All Child B")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child_a["child_id"])
    _link_parent_to_child(db_session, parent_id=other_parent["parent"].parent_id, child_id=child_b["child_id"])

    response = client.post(
        "/api/v1/announcements/",
        json={"title": "Holiday", "message": "Bog'cha yopiq.", "target_type": "all"},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert response.json()["target_type"] == "all"


def test_kindergarten_can_create_announcement_for_group_target(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Group Announcement Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Group Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    response = client.post(
        "/api/v1/announcements/",
        json={
            "title": "Group Event",
            "message": "Faqat guruh uchun.",
            "target_type": "group",
            "target_group_id": group["group_id"],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert response.json()["target_group_id"] == group["group_id"]


def test_kindergarten_can_create_announcement_for_child_target(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Child Announcement Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Child Target")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    response = client.post(
        "/api/v1/announcements/",
        json={
            "title": "Child Note",
            "message": "Bolaga oid e'lon.",
            "target_type": "child",
            "target_child_id": child["child_id"],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert response.json()["target_child_id"] == child["child_id"]


def test_announcement_fan_out_creates_correct_number_of_parent_notifications(
    client,
    verified_tenant,
    parent_account,
    parent_factory,
    db_session,
    create_group,
    create_child,
):
    second_parent = parent_factory()
    group = create_group(verified_tenant, name="Fanout Group")
    child_a = create_child(verified_tenant, group["group_id"], full_name="Fanout Child A")
    child_b = create_child(verified_tenant, group["group_id"], full_name="Fanout Child B")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child_a["child_id"])
    _link_parent_to_child(db_session, parent_id=second_parent["parent"].parent_id, child_id=child_b["child_id"])

    response = client.post(
        "/api/v1/announcements/",
        json={"title": "All Hands", "message": "Umumiy e'lon.", "target_type": "all"},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    announcement_id = response.json()["id"]
    notifications = (
        db_session.query(Notification)
        .filter(Notification.source_announcement_id == announcement_id)
        .all()
    )
    stats = (
        db_session.query(NotificationDeliveryStats)
        .filter(NotificationDeliveryStats.announcement_id == announcement_id)
        .one()
    )
    assert len(notifications) == 2
    assert stats.sent_count == 2
    assert {item.parent_id for item in notifications} == {
        parent_account["parent"].parent_id,
        second_parent["parent"].parent_id,
    }


def test_parent_only_sees_own_notifications(
    client,
    verified_tenant,
    parent_account,
    parent_factory,
    db_session,
    create_group,
    create_child,
):
    other_parent = parent_factory()
    group = create_group(verified_tenant, name="Own Notifications Group")
    child_a = create_child(verified_tenant, group["group_id"], full_name="Visible Child")
    child_b = create_child(verified_tenant, group["group_id"], full_name="Hidden Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child_a["child_id"])
    _link_parent_to_child(db_session, parent_id=other_parent["parent"].parent_id, child_id=child_b["child_id"])

    _create_payment(client, verified_tenant, child_id=child_a["child_id"], billing_period="2026-06")
    _create_payment(client, verified_tenant, child_id=child_b["child_id"], billing_period="2026-07")

    response = client.get("/api/v1/parent/notifications", headers=parent_account["headers"])

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["parent_id"] == parent_account["parent"].parent_id


def test_parent_can_mark_notification_as_read(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Read Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Read Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-08")
    notification = db_session.query(Notification).one()

    response = client.patch(
        f"/api/v1/parent/notifications/{notification.id}/read",
        headers=parent_account["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["is_read"] is True
    assert response.json()["read_at"] is not None


def test_parent_notification_settings_are_readable_and_updatable(
    client,
    parent_account,
    db_session,
):
    get_response = client.get("/api/v1/parent/notification-settings", headers=parent_account["headers"])

    assert get_response.status_code == status.HTTP_200_OK, get_response.text
    assert get_response.json()["attendance_enabled"] is True
    assert get_response.json()["telegram_enabled"] is True

    patch_response = client.patch(
        "/api/v1/parent/notification-settings",
        json={"attendance_enabled": False, "telegram_enabled": False},
        headers=parent_account["headers"],
    )

    assert patch_response.status_code == status.HTTP_200_OK, patch_response.text
    settings_row = db_session.query(ParentNotificationSettings).filter_by(parent_id=parent_account["parent"].parent_id).one()
    assert settings_row.attendance_enabled is False
    assert settings_row.telegram_enabled is False


def test_tenant_isolation_blocks_foreign_announcement_access(
    client,
    verified_tenant,
    second_verified_tenant,
):
    create_response = client.post(
        "/api/v1/announcements/",
        json={"title": "Tenant A", "message": "Private", "target_type": "all"},
        headers=verified_tenant["headers"],
    )
    announcement_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/announcements/{announcement_id}", headers=second_verified_tenant["headers"])
    delete_response = client.delete(f"/api/v1/announcements/{announcement_id}", headers=second_verified_tenant["headers"])

    assert get_response.status_code == status.HTTP_403_FORBIDDEN
    assert delete_response.status_code == status.HTTP_403_FORBIDDEN


def test_telegram_failure_does_not_break_main_api_flow(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    monkeypatch,
):
    group = create_group(verified_tenant, name="Telegram Failure Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Telegram Failure Child")
    parent_account["parent"].telegram_id = "123456"
    db_session.add(parent_account["parent"])
    db_session.commit()
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "test-token", raising=False)

    def _raise(*args, **kwargs):
        raise RuntimeError("telegram offline")

    monkeypatch.setattr("app.services.telegram_service.httpx.post", _raise)

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-04-05",
            "records": [{"child_id": child["child_id"], "status": "late"}],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    notification = db_session.query(Notification).one()
    assert notification.telegram_delivery_status == TelegramDeliveryStatus.FAILED
    assert notification.is_read is False


def test_category_preferences_skip_telegram_but_keep_in_app_notification(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Preference Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Preference Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    update_response = client.patch(
        "/api/v1/parent/notification-settings",
        json={"attendance_enabled": False},
        headers=parent_account["headers"],
    )
    assert update_response.status_code == status.HTTP_200_OK, update_response.text

    response = client.post(
        "/api/v1/attendance/bulk",
        json={
            "group_id": group["group_id"],
            "date": "2026-04-06",
            "records": [{"child_id": child["child_id"], "status": "late"}],
        },
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    notification = db_session.query(Notification).one()
    assert notification.event_type == NotificationEventType.ATTENDANCE_LATE
    assert notification.telegram_delivery_status == TelegramDeliveryStatus.SKIPPED
    list_response = client.get("/api/v1/parent/notifications", headers=parent_account["headers"])
    assert list_response.json()["total"] == 1


def test_announcement_read_updates_delivery_stats(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Stats Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Stats Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    create_response = client.post(
        "/api/v1/announcements/",
        json={"title": "Stats", "message": "Read me", "target_type": "all"},
        headers=verified_tenant["headers"],
    )
    assert create_response.status_code == status.HTTP_201_CREATED, create_response.text
    announcement = db_session.query(Announcement).filter_by(id=create_response.json()["id"]).one()
    notification = db_session.query(Notification).filter_by(source_announcement_id=announcement.id).one()

    read_response = client.patch(
        f"/api/v1/parent/notifications/{notification.id}/read",
        headers=parent_account["headers"],
    )

    assert read_response.status_code == status.HTTP_200_OK, read_response.text
    stats = db_session.query(NotificationDeliveryStats).filter_by(announcement_id=announcement.id).one()
    assert stats.read_count == 1
