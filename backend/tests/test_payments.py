"""Tests for milestone 5 payment tracking."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import status

from app.models.child import ParentChildLink
from app.models.notification import Notification, NotificationEventType


def _link_parent_to_child(db_session, *, parent_id: str, child_id: str, note: str = "Linked for billing") -> None:
    db_session.add(
        ParentChildLink(
            link_id=f"link-{parent_id[:8]}-{child_id[:8]}",
            parent_id=parent_id,
            child_id=child_id,
            note=note,
            status="active",
        )
    )
    db_session.commit()


def _create_payment(client, tenant, *, child_id: str, amount="250000.00", due_date=None, billing_period="2026-04", **extra):
    due = due_date or (date.today() + timedelta(days=5)).isoformat()
    payload = {
        "child_id": child_id,
        "amount": amount,
        "due_date": due,
        "billing_period": billing_period,
        "status": "pending",
        **extra,
    }
    return client.post("/api/v1/payments/", json=payload, headers=tenant["headers"])


def test_kindergarten_creates_payment_record_successfully(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Payments Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Billing Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    response = _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-04")

    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["child_id"] == child["child_id"]
    assert data["status"] == "pending"
    assert data["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id
    notifications = db_session.query(Notification).all()
    assert len(notifications) == 1
    assert notifications[0].event_type == NotificationEventType.PAYMENT_CREATED


def test_duplicate_billing_period_for_same_child_is_rejected(
    client,
    verified_tenant,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Duplicate Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Duplicate Child")

    first_response = _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-04")
    second_response = _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-04")

    assert first_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_409_CONFLICT


def test_parent_can_see_only_linked_child_payments(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Parent Visible Group")
    visible_child = create_child(verified_tenant, group["group_id"], full_name="Visible Child")
    hidden_child = create_child(verified_tenant, group["group_id"], full_name="Hidden Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=visible_child["child_id"])

    visible_payment = _create_payment(client, verified_tenant, child_id=visible_child["child_id"], billing_period="2026-04")
    hidden_payment = _create_payment(client, verified_tenant, child_id=hidden_child["child_id"], billing_period="2026-05")
    assert visible_payment.status_code == status.HTTP_201_CREATED
    assert hidden_payment.status_code == status.HTTP_201_CREATED

    response = client.get("/api/v1/parent/payments", headers=parent_account["headers"])

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["child_id"] == visible_child["child_id"]


def test_parent_cannot_see_another_parents_child_payment(
    client,
    verified_tenant,
    parent_account,
    parent_factory,
    db_session,
    create_group,
    create_child,
):
    other_parent = parent_factory()
    group = create_group(verified_tenant, name="Restricted Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Restricted Child")
    _link_parent_to_child(db_session, parent_id=other_parent["parent"].parent_id, child_id=child["child_id"])
    payment_response = _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-04")
    payment_id = payment_response.json()["payment_id"]

    response = client.get(f"/api/v1/parent/payments/{payment_id}", headers=parent_account["headers"])

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_overdue_logic_works_correctly(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Overdue Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Overdue Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    payment_response = _create_payment(
        client,
        verified_tenant,
        child_id=child["child_id"],
        billing_period="2026-01",
        due_date=(date.today() - timedelta(days=2)).isoformat(),
    )
    payment_id = payment_response.json()["payment_id"]

    response = client.get(f"/api/v1/payments/{payment_id}", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "overdue"
    overdue_notifications = (
        db_session.query(Notification)
        .filter(Notification.event_type == NotificationEventType.PAYMENT_OVERDUE)
        .all()
    )
    assert len(overdue_notifications) == 1


def test_mark_paid_updates_status_and_paid_at(
    client,
    verified_tenant,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Paid Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Paid Child")
    payment_response = _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-04")
    payment_id = payment_response.json()["payment_id"]

    response = client.patch(
        f"/api/v1/payments/{payment_id}/mark-paid",
        json={"payment_method": "cash"},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "paid"
    assert data["paid_at"] is not None
    assert data["payment_method"] == "cash"


def test_cross_tenant_payment_access_is_rejected(
    client,
    verified_tenant,
    second_verified_tenant,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Tenant A Payments")
    child = create_child(verified_tenant, group["group_id"], full_name="Tenant A Child")
    payment_response = _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-04")
    payment_id = payment_response.json()["payment_id"]

    response = client.get(f"/api/v1/payments/{payment_id}", headers=second_verified_tenant["headers"])

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_payment_list_filters_work(
    client,
    verified_tenant,
    create_group,
    create_child,
):
    group_a = create_group(verified_tenant, name="Filter A")
    group_b = create_group(verified_tenant, name="Filter B")
    child_a = create_child(verified_tenant, group_a["group_id"], full_name="Filter Child A")
    child_b = create_child(verified_tenant, group_b["group_id"], full_name="Filter Child B")
    _create_payment(
        client,
        verified_tenant,
        child_id=child_a["child_id"],
        billing_period="2026-04",
        due_date=(date.today() + timedelta(days=3)).isoformat(),
    )
    paid_payment = _create_payment(
        client,
        verified_tenant,
        child_id=child_b["child_id"],
        billing_period="2026-05",
        status="paid",
        payment_method="bank_transfer",
    )
    assert paid_payment.status_code == status.HTTP_201_CREATED

    response = client.get(
        f"/api/v1/payments/?group_id={group_b['group_id']}&status=paid&billing_period=2026-05",
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["child_id"] == child_b["child_id"]
    assert data["items"][0]["status"] == "paid"


def test_already_paid_record_does_not_become_overdue(
    client,
    verified_tenant,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Already Paid Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Already Paid Child")
    response = _create_payment(
        client,
        verified_tenant,
        child_id=child["child_id"],
        billing_period="2025-12",
        due_date=(date.today() - timedelta(days=10)).isoformat(),
        status="paid",
        payment_method="click",
    )
    payment_id = response.json()["payment_id"]

    get_response = client.get(f"/api/v1/payments/{payment_id}", headers=verified_tenant["headers"])

    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["status"] == "paid"


def test_payment_creation_integrates_with_existing_auth_and_tenant_rules(
    client,
    unverified_tenant,
    second_verified_tenant,
    create_group,
    create_child,
):
    tenant_a_group = create_group(second_verified_tenant, name="Foreign Group")
    tenant_a_child = create_child(second_verified_tenant, tenant_a_group["group_id"], full_name="Foreign Child")

    unverified_response = _create_payment(client, unverified_tenant, child_id=tenant_a_child["child_id"], billing_period="2026-04")
    foreign_response = _create_payment(client, second_verified_tenant, child_id=tenant_a_child["child_id"], billing_period="2026-04")

    assert unverified_response.status_code == status.HTTP_403_FORBIDDEN
    assert foreign_response.status_code == status.HTTP_201_CREATED


def test_parent_payment_detail_returns_linked_record(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Parent Detail Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Parent Detail Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    payment_response = _create_payment(client, verified_tenant, child_id=child["child_id"], billing_period="2026-04")
    payment_id = payment_response.json()["payment_id"]

    response = client.get(f"/api/v1/parent/payments/{payment_id}", headers=parent_account["headers"])

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["child_name"] == "Parent Detail Child"


def test_payment_report_export_success_and_empty_report(
    client,
    verified_tenant,
    create_group,
    create_child,
):
    empty_response = client.get("/api/v1/reports/payments/export?period=daily", headers=verified_tenant["headers"])
    assert empty_response.status_code == status.HTTP_200_OK
    assert empty_response.headers["content-type"] == "application/pdf"
    assert b"No payment data found" in empty_response.content

    group = create_group(verified_tenant, name="Report Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Report Child")
    create_response = _create_payment(
        client,
        verified_tenant,
        child_id=child["child_id"],
        billing_period=f"{date.today().year:04d}-{date.today().month:02d}",
        due_date=date.today().isoformat(),
    )
    assert create_response.status_code == status.HTTP_201_CREATED

    response = client.get("/api/v1/reports/payments/export?period=daily", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-1.4")
    assert b"Report Child" in response.content


def test_payment_report_export_authorization_and_tenant_isolation(
    client,
    verified_tenant,
    second_verified_tenant,
    parent_account,
    create_group,
    create_child,
):
    group_a = create_group(verified_tenant, name="Report Tenant A")
    child_a = create_child(verified_tenant, group_a["group_id"], full_name="Tenant A Export Child")
    group_b = create_group(second_verified_tenant, name="Report Tenant B")
    create_child(second_verified_tenant, group_b["group_id"], full_name="Tenant B Export Child")
    create_response = _create_payment(
        client,
        verified_tenant,
        child_id=child_a["child_id"],
        billing_period=f"{date.today().year:04d}-{date.today().month:02d}",
        due_date=date.today().isoformat(),
    )
    assert create_response.status_code == status.HTTP_201_CREATED

    parent_response = client.get("/api/v1/reports/payments/export?period=daily", headers=parent_account["headers"])
    tenant_response = client.get("/api/v1/reports/payments/export?period=daily", headers=verified_tenant["headers"])

    assert parent_response.status_code == status.HTTP_403_FORBIDDEN
    assert tenant_response.status_code == status.HTTP_200_OK
    assert b"Tenant A Export Child" in tenant_response.content
    assert b"Tenant B Export Child" not in tenant_response.content
