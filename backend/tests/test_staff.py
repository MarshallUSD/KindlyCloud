"""Milestone 3 staff and pedagogue integration tests."""
try:
    from . import _bootstrap  # noqa: F401
except ImportError:  # pragma: no cover - direct script execution fallback
    import _bootstrap  # type: ignore  # noqa: F401

from fastapi import status


def test_create_staff_successfully(client, verified_tenant, create_group, staff_payload):
    group = create_group(verified_tenant)

    response = client.post(
        "/api/v1/staff/",
        json={**staff_payload, "group_id": group["group_id"]},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id
    assert data["group_id"] == group["group_id"]
    assert data["role"] == staff_payload["role"]


def test_invalid_staff_payload_rejected(client, verified_tenant):
    response = client.post(
        "/api/v1/staff/",
        json={"full_name": "Broken Staff", "role": "teacher"},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_staff_only_returns_current_tenant_data(
    client, verified_tenant, second_verified_tenant, create_group, create_staff
):
    own_group = create_group(verified_tenant)
    other_group = create_group(second_verified_tenant)
    own_staff = create_staff(verified_tenant, group_id=own_group["group_id"], full_name="Tenant A Staff")
    create_staff(second_verified_tenant, group_id=other_group["group_id"], full_name="Tenant B Staff")

    response = client.get("/api/v1/staff/", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert [item["teacher_id"] for item in data["items"]] == [own_staff["teacher_id"]]
    assert all(item["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id for item in data["items"])


def test_cross_tenant_staff_relation_attempt_rejected(
    client, verified_tenant, second_verified_tenant, create_group, staff_payload
):
    foreign_group = create_group(second_verified_tenant)

    response = client.post(
        "/api/v1/staff/",
        json={**staff_payload, "group_id": foreign_group["group_id"]},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "You cannot use a group from another kindergarten"


def test_update_and_delete_staff_if_implemented(client, verified_tenant, create_group, create_staff):
    original_group = create_group(verified_tenant, name="Staff Original Group")
    new_group = create_group(verified_tenant, name="Staff New Group")
    staff_member = create_staff(verified_tenant, group_id=original_group["group_id"])

    update_response = client.put(
        f"/api/v1/staff/{staff_member['teacher_id']}",
        json={"role": "assistant", "group_id": new_group["group_id"]},
        headers=verified_tenant["headers"],
    )
    updated_group_response = client.get(
        f"/api/v1/groups/{new_group['group_id']}",
        headers=verified_tenant["headers"],
    )

    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["role"] == "assistant"
    assert update_response.json()["group_id"] == new_group["group_id"]
    assert updated_group_response.status_code == status.HTTP_200_OK
    assert updated_group_response.json()["teacher_id"] == staff_member["teacher_id"]

    delete_response = client.delete(
        f"/api/v1/staff/{staff_member['teacher_id']}",
        headers=verified_tenant["headers"],
    )
    get_after_delete_response = client.get(
        f"/api/v1/staff/{staff_member['teacher_id']}",
        headers=verified_tenant["headers"],
    )

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert get_after_delete_response.status_code == status.HTTP_404_NOT_FOUND
