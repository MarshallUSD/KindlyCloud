"""Milestone 2 group integration tests."""
try:
    from . import _bootstrap  # noqa: F401
except ImportError:  # pragma: no cover - direct script execution fallback
    import _bootstrap  # type: ignore  # noqa: F401

from fastapi import status


def test_create_group_successfully(client, verified_tenant, group_payload):
    response = client.post("/api/v1/groups/", json=group_payload, headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == group_payload["name"]
    assert data["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id
    assert data["teacher_id"] is None


def test_invalid_group_payload_rejected(client, verified_tenant, group_payload):
    invalid_payload = {**group_payload, "age_from": 6, "age_to": 4}

    response = client.post("/api/v1/groups/", json=invalid_payload, headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_groups_only_returns_current_tenant_groups(client, verified_tenant, second_verified_tenant, create_group):
    own_group = create_group(verified_tenant, name="Tenant A Group")
    create_group(second_verified_tenant, name="Tenant B Group")

    response = client.get("/api/v1/groups/", headers=verified_tenant["headers"])

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert [item["group_id"] for item in data["items"]] == [own_group["group_id"]]
    assert all(item["kindergarten_id"] == verified_tenant["kindergarten"].kindergarten_id for item in data["items"])


def test_tenant_b_cannot_access_update_or_delete_tenant_a_group(
    client, verified_tenant, second_verified_tenant, create_group
):
    tenant_a_group = create_group(verified_tenant)

    get_response = client.get(
        f"/api/v1/groups/{tenant_a_group['group_id']}",
        headers=second_verified_tenant["headers"],
    )
    update_response = client.put(
        f"/api/v1/groups/{tenant_a_group['group_id']}",
        json={"capacity": 25},
        headers=second_verified_tenant["headers"],
    )
    delete_response = client.delete(
        f"/api/v1/groups/{tenant_a_group['group_id']}",
        headers=second_verified_tenant["headers"],
    )

    assert get_response.status_code == status.HTTP_404_NOT_FOUND
    assert update_response.status_code == status.HTTP_404_NOT_FOUND
    assert delete_response.status_code == status.HTTP_404_NOT_FOUND


def test_unverified_kindergarten_cannot_use_verified_group_routes(client, unverified_tenant, group_payload):
    response = client.post("/api/v1/groups/", json=group_payload, headers=unverified_tenant["headers"])

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Kindergarten account is pending verification"
