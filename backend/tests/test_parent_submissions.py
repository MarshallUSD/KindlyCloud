"""Tests for parent submissions and Telegram payment proof intake."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi import status

from config import settings
from app.core.time import utcnow
from app.models.child import ParentChildLink
from app.models.parent_submission import ParentSubmission
from app.models.payment import Payment


def _link_parent_to_child(db_session, *, parent_id: str, child_id: str, note: str = "Linked for submissions") -> None:
    db_session.add(
        ParentChildLink(
            link_id=f"submission-link-{parent_id[:8]}-{child_id[:8]}",
            parent_id=parent_id,
            child_id=child_id,
            note=note,
            status="active",
        )
    )
    db_session.commit()


def _create_payment(client, tenant, *, child_id: str, amount="250000.00", due_date=None, billing_period="2026-04", **extra):
    payload = {
        "child_id": child_id,
        "amount": amount,
        "due_date": due_date or (date.today() + timedelta(days=5)).isoformat(),
        "billing_period": billing_period,
        "status": "pending",
        **extra,
    }
    response = client.post("/api/v1/payments/", json=payload, headers=tenant["headers"])
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def _create_submission(client, *, secret: str, payload: dict):
    return client.post(
        "/api/v1/integrations/telegram/parent-submissions",
        json=payload,
        headers={"X-Integration-Secret": secret},
    )


@pytest.fixture(autouse=True)
def telegram_submission_secret():
    """Set the integration secret for tests."""
    previous = settings.TELEGRAM_PARENT_SUBMISSIONS_SECRET
    settings.TELEGRAM_PARENT_SUBMISSIONS_SECRET = "test-parent-submission-secret"
    yield settings.TELEGRAM_PARENT_SUBMISSIONS_SECRET
    settings.TELEGRAM_PARENT_SUBMISSIONS_SECRET = previous


def test_integration_creates_submission_successfully_with_valid_secret(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group = create_group(verified_tenant, name="Inbox Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Inbox Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    parent_account["parent"].telegram_id = "tg-parent-1"
    db_session.add(parent_account["parent"])
    db_session.commit()

    response = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_telegram_id": "tg-parent-1",
            "child_id": child["child_id"],
            "submission_type": "message",
            "text": "Please review this note",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id
    assert data["parent_id"] == parent_account["parent"].parent_id
    assert data["child_id"] == child["child_id"]
    assert data["status"] == "pending"


def test_integration_rejects_request_with_invalid_or_missing_secret(
    client,
    verified_tenant,
    parent_account,
    telegram_submission_secret,
):
    payload = {
        "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
        "parent_id": parent_account["parent"].parent_id,
        "submission_type": "message",
        "text": "No secret",
    }

    missing = client.post("/api/v1/integrations/telegram/parent-submissions", json=payload)
    invalid = _create_submission(client, secret="wrong-secret", payload=payload)

    assert missing.status_code == status.HTTP_401_UNAUTHORIZED
    assert invalid.status_code == status.HTTP_401_UNAUTHORIZED


def test_integration_rejects_cross_tenant_or_invalid_parent_payment_relations(
    client,
    verified_tenant,
    second_verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group_a = create_group(verified_tenant, name="Tenant A Submissions")
    child_a = create_child(verified_tenant, group_a["group_id"], full_name="Tenant A Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child_a["child_id"])
    group_b = create_group(second_verified_tenant, name="Tenant B Submissions")
    child_b = create_child(second_verified_tenant, group_b["group_id"], full_name="Tenant B Child")
    payment_b = _create_payment(client, second_verified_tenant, child_id=child_b["child_id"], billing_period="2026-05")

    response = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": second_verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "payment_id": payment_b["payment_id"],
            "submission_type": "payment_proof",
            "attachment_url": "https://files.example.com/proof.png",
            "attachment_type": "image",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Parent is not linked" in response.json()["detail"]


def test_integration_creates_submission_with_text_only(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group = create_group(verified_tenant, name="Text Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Text Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    response = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "submission_type": "message",
            "text": "Text only submission",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["text"] == "Text only submission"
    assert response.json()["attachment_url"] is None


def test_integration_creates_submission_with_attachment_only(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group = create_group(verified_tenant, name="Attachment Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Attachment Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    response = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "child_id": child["child_id"],
            "submission_type": "other",
            "attachment_url": "https://files.example.com/file.pdf",
            "attachment_type": "document",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["text"] is None
    assert response.json()["attachment_type"] == "document"


def test_integration_creates_submission_linked_to_payment(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group = create_group(verified_tenant, name="Payment Proof Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Payment Proof Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    payment = _create_payment(client, verified_tenant, child_id=child["child_id"])

    response = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "payment_id": payment["payment_id"],
            "submission_type": "payment_proof",
            "attachment_url": "https://files.example.com/payment-proof.png",
            "attachment_type": "screenshot",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["payment_id"] == payment["payment_id"]
    assert response.json()["child_id"] == child["child_id"]


def test_kindergarten_list_and_detail_are_tenant_scoped(
    client,
    verified_tenant,
    second_verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group_a = create_group(verified_tenant, name="Tenant Scoped A")
    child_a = create_child(verified_tenant, group_a["group_id"], full_name="Scoped Child A")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child_a["child_id"])
    response = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "child_id": child_a["child_id"],
            "submission_type": "message",
            "text": "Tenant scoped inbox item",
        },
    )
    submission_id = response.json()["id"]

    own_list = client.get("/api/v1/parent-submissions", headers=verified_tenant["headers"])
    own_detail = client.get(f"/api/v1/parent-submissions/{submission_id}", headers=verified_tenant["headers"])
    foreign_detail = client.get(f"/api/v1/parent-submissions/{submission_id}", headers=second_verified_tenant["headers"])

    assert own_list.status_code == status.HTTP_200_OK
    assert own_list.json()["total"] == 1
    assert own_detail.status_code == status.HTTP_200_OK
    assert foreign_detail.status_code == status.HTTP_403_FORBIDDEN


def test_review_flow_marks_submission_reviewed_approved_and_rejected(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group = create_group(verified_tenant, name="Review Flow Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Review Flow Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])

    reviewed_submission = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "submission_type": "message",
            "text": "Review me",
        },
    ).json()
    approved_submission = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "submission_type": "message",
            "text": "Approve me",
        },
    ).json()
    rejected_submission = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "submission_type": "message",
            "text": "Reject me",
        },
    ).json()

    reviewed = client.patch(
        f"/api/v1/parent-submissions/{reviewed_submission['id']}/review",
        json={"action": "reviewed", "admin_note": "Seen by staff"},
        headers=verified_tenant["headers"],
    )
    approved = client.patch(
        f"/api/v1/parent-submissions/{approved_submission['id']}/review",
        json={"action": "approved", "admin_note": "Accepted"},
        headers=verified_tenant["headers"],
    )
    rejected = client.patch(
        f"/api/v1/parent-submissions/{rejected_submission['id']}/review",
        json={"action": "rejected", "admin_note": "Not valid"},
        headers=verified_tenant["headers"],
    )

    assert reviewed.status_code == status.HTTP_200_OK
    assert reviewed.json()["status"] == "reviewed"
    assert reviewed.json()["reviewed_at"] is not None
    assert approved.status_code == status.HTTP_200_OK
    assert approved.json()["status"] == "approved"
    assert rejected.status_code == status.HTTP_200_OK
    assert rejected.json()["status"] == "rejected"


def test_approve_payment_proof_submission_updates_payment_status_correctly(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group = create_group(verified_tenant, name="Payment Approve Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Payment Approve Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    payment = _create_payment(client, verified_tenant, child_id=child["child_id"])
    submission = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "payment_id": payment["payment_id"],
            "submission_type": "payment_proof",
            "attachment_url": "https://files.example.com/proof.png",
            "attachment_type": "image",
        },
    ).json()

    response = client.patch(
        f"/api/v1/parent-submissions/{submission['id']}/review",
        json={"action": "approved", "admin_note": "Payment confirmed"},
        headers=verified_tenant["headers"],
    )
    payment_detail = client.get(f"/api/v1/payments/{payment['payment_id']}", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "approved"
    assert payment_detail.status_code == status.HTTP_200_OK
    assert payment_detail.json()["status"] == "paid"


def test_reject_payment_proof_submission_does_not_mark_payment_paid(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group = create_group(verified_tenant, name="Payment Reject Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Payment Reject Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    payment = _create_payment(client, verified_tenant, child_id=child["child_id"])
    submission = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "payment_id": payment["payment_id"],
            "submission_type": "payment_proof",
            "attachment_url": "https://files.example.com/proof.png",
            "attachment_type": "image",
        },
    ).json()

    response = client.patch(
        f"/api/v1/parent-submissions/{submission['id']}/review",
        json={"action": "rejected", "admin_note": "Proof is unreadable"},
        headers=verified_tenant["headers"],
    )
    payment_detail = client.get(f"/api/v1/payments/{payment['payment_id']}", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "rejected"
    assert payment_detail.json()["status"] == "pending"


def test_invalid_review_transition_is_handled_safely(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    group = create_group(verified_tenant, name="Transition Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Transition Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    submission = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "submission_type": "message",
            "text": "Transition test",
        },
    ).json()

    first = client.patch(
        f"/api/v1/parent-submissions/{submission['id']}/review",
        json={"action": "approved", "admin_note": "Final approval"},
        headers=verified_tenant["headers"],
    )
    second = client.patch(
        f"/api/v1/parent-submissions/{submission['id']}/review",
        json={"action": "rejected", "admin_note": "Should fail"},
        headers=verified_tenant["headers"],
    )
    repeat = client.patch(
        f"/api/v1/parent-submissions/{submission['id']}/review",
        json={"action": "approved", "admin_note": "Still approved"},
        headers=verified_tenant["headers"],
    )

    assert first.status_code == status.HTTP_200_OK
    assert second.status_code == status.HTTP_400_BAD_REQUEST
    assert repeat.status_code == status.HTTP_200_OK
    assert repeat.json()["status"] == "approved"


def test_submission_filters_and_pagination_work(
    client,
    verified_tenant,
    parent_account,
    parent_factory,
    db_session,
    create_group,
    create_child,
    telegram_submission_secret,
):
    second_parent = parent_factory()
    group = create_group(verified_tenant, name="Filter Submission Group")
    child_a = create_child(verified_tenant, group["group_id"], full_name="Filter Child A")
    child_b = create_child(verified_tenant, group["group_id"], full_name="Filter Child B")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child_a["child_id"])
    _link_parent_to_child(db_session, parent_id=second_parent["parent"].parent_id, child_id=child_b["child_id"])
    payment = _create_payment(client, verified_tenant, child_id=child_a["child_id"], billing_period="2026-06")

    first = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": parent_account["parent"].parent_id,
            "child_id": child_a["child_id"],
            "payment_id": payment["payment_id"],
            "submission_type": "payment_proof",
            "text": "Payment proof text",
        },
    ).json()
    second = _create_submission(
        client,
        secret=telegram_submission_secret,
        payload={
            "kindergarten_id": verified_tenant["kindergarten"].kindergarten_id,
            "parent_id": second_parent["parent"].parent_id,
            "child_id": child_b["child_id"],
            "submission_type": "message",
            "text": "General message",
        },
    ).json()
    client.patch(
        f"/api/v1/parent-submissions/{second['id']}/review",
        json={"action": "reviewed", "admin_note": "Reviewed for filter"},
        headers=verified_tenant["headers"],
    )

    older_submission = db_session.query(ParentSubmission).filter(ParentSubmission.id == first["id"]).one()
    older_submission.created_at = utcnow() - timedelta(days=3)
    db_session.add(older_submission)
    db_session.commit()

    by_status = client.get("/api/v1/parent-submissions?status=reviewed", headers=verified_tenant["headers"])
    by_type = client.get("/api/v1/parent-submissions?submission_type=payment_proof", headers=verified_tenant["headers"])
    by_parent = client.get(
        f"/api/v1/parent-submissions?parent_id={parent_account['parent'].parent_id}",
        headers=verified_tenant["headers"],
    )
    by_child = client.get(f"/api/v1/parent-submissions?child_id={child_a['child_id']}", headers=verified_tenant["headers"])
    by_payment = client.get(f"/api/v1/parent-submissions?payment_id={payment['payment_id']}", headers=verified_tenant["headers"])
    by_date = client.get(
        f"/api/v1/parent-submissions?date_from={(date.today() - timedelta(days=1)).isoformat()}",
        headers=verified_tenant["headers"],
    )
    paged = client.get("/api/v1/parent-submissions?page=2&size=1", headers=verified_tenant["headers"])

    assert by_status.status_code == status.HTTP_200_OK
    assert by_status.json()["total"] == 1
    assert by_status.json()["items"][0]["id"] == second["id"]
    assert by_type.json()["total"] == 1
    assert by_type.json()["items"][0]["id"] == first["id"]
    assert by_parent.json()["total"] == 1
    assert by_child.json()["total"] == 1
    assert by_payment.json()["total"] == 1
    assert by_date.json()["total"] == 1
    assert paged.json()["total"] == 2
    assert len(paged.json()["items"]) == 1


def test_payment_and_parent_endpoints_still_work_with_submission_module_present(
    client,
    verified_tenant,
    parent_account,
    db_session,
    create_group,
    create_child,
):
    group = create_group(verified_tenant, name="Regression Group")
    child = create_child(verified_tenant, group["group_id"], full_name="Regression Child")
    _link_parent_to_child(db_session, parent_id=parent_account["parent"].parent_id, child_id=child["child_id"])
    payment = _create_payment(client, verified_tenant, child_id=child["child_id"])

    tenant_payment = client.get(f"/api/v1/payments/{payment['payment_id']}", headers=verified_tenant["headers"])
    parent_children = client.get("/api/v1/parent/children", headers=parent_account["headers"])

    assert tenant_payment.status_code == status.HTTP_200_OK
    assert parent_children.status_code == status.HTTP_200_OK
