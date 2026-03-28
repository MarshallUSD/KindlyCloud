"""Milestone 3 child management integration tests."""
try:
    from . import _bootstrap  # noqa: F401
except ImportError:  # pragma: no cover - direct script execution fallback
    import _bootstrap  # type: ignore  # noqa: F401

from datetime import date
import uuid

from fastapi import status

from app.models.group import Group


def test_create_child_successfully_under_valid_tenant_group(
    client, verified_tenant, create_group, child_payload
):
    group = create_group(verified_tenant)

    response = client.post(
        "/api/v1/children/",
        json={**child_payload, "group_id": group["group_id"]},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["group_id"] == group["group_id"]
    assert data["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id
    assert data["full_name"] == child_payload["full_name"]


def test_create_child_with_invalid_group_rejected(client, verified_tenant, child_payload):
    response = client.post(
        "/api/v1/children/",
        json={**child_payload, "group_id": str(uuid.uuid4())},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Group not found in your kindergarten"


def test_create_child_in_another_tenants_group_rejected(
    client, verified_tenant, second_verified_tenant, create_group, child_payload
):
    foreign_group = create_group(second_verified_tenant)

    response = client.post(
        "/api/v1/children/",
        json={**child_payload, "group_id": foreign_group["group_id"]},
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "You cannot use a group from another kindergarten"


def test_list_children_only_returns_current_tenant_data(
    client, verified_tenant, second_verified_tenant, create_group, create_child
):
    own_group = create_group(verified_tenant)
    other_group = create_group(second_verified_tenant)
    own_child = create_child(verified_tenant, own_group["group_id"], full_name="Tenant A Child")
    create_child(second_verified_tenant, other_group["group_id"], full_name="Tenant B Child")

    response = client.get("/api/v1/children/", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert [item["child_id"] for item in data["items"]] == [own_child["child_id"]]
    assert all(item["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id for item in data["items"])


def test_update_and_delete_child_if_implemented(client, verified_tenant, create_group, create_child):
    original_group = create_group(verified_tenant, name="Original Group")
    new_group = create_group(verified_tenant, name="New Group")
    child = create_child(verified_tenant, original_group["group_id"])

    update_response = client.put(
        f"/api/v1/children/{child['child_id']}",
        json={"group_id": new_group["group_id"], "notes": "Updated notes"},
        headers=verified_tenant["headers"],
    )

    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["group_id"] == new_group["group_id"]
    assert update_response.json()["notes"] == "Updated notes"

    delete_response = client.delete(
        f"/api/v1/children/{child['child_id']}",
        headers=verified_tenant["headers"],
    )
    get_after_delete_response = client.get(
        f"/api/v1/children/{child['child_id']}",
        headers=verified_tenant["headers"],
    )

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert get_after_delete_response.status_code == status.HTTP_404_NOT_FOUND


def test_child_list_group_filter_rejects_foreign_group(
    client, verified_tenant, second_verified_tenant, create_group
):
    foreign_group = create_group(second_verified_tenant)

    response = client.get(
        f"/api/v1/children/?group_id={foreign_group['group_id']}",
        headers=verified_tenant["headers"],
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "You cannot use a group from another kindergarten"
