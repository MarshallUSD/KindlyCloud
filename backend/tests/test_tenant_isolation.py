"""Milestone 2-3 tenant isolation integration tests."""
try:
    from . import _bootstrap  # noqa: F401
except ImportError:  # pragma: no cover - direct script execution fallback
    import _bootstrap  # type: ignore  # noqa: F401

from fastapi import status


def test_negative_path_tenant_isolation_for_group_child_and_staff_resources(
    client,
    verified_tenant,
    second_verified_tenant,
    create_group,
    create_child,
    create_staff,
):
    tenant_a_group = create_group(verified_tenant, name="Tenant A Protected Group")
    tenant_a_child = create_child(verified_tenant, tenant_a_group["group_id"], full_name="Tenant A Child")
    tenant_a_staff = create_staff(verified_tenant, group_id=tenant_a_group["group_id"], full_name="Tenant A Staff")

    group_get = client.get(
        f"/api/v1/groups/{tenant_a_group['group_id']}",
        headers=second_verified_tenant["headers"],
    )
    group_update = client.put(
        f"/api/v1/groups/{tenant_a_group['group_id']}",
        json={"name": "Illegal Update"},
        headers=second_verified_tenant["headers"],
    )
    child_get = client.get(
        f"/api/v1/children/{tenant_a_child['child_id']}",
        headers=second_verified_tenant["headers"],
    )
    child_update = client.put(
        f"/api/v1/children/{tenant_a_child['child_id']}",
        json={"notes": "Illegal Update"},
        headers=second_verified_tenant["headers"],
    )
    staff_get = client.get(
        f"/api/v1/staff/{tenant_a_staff['teacher_id']}",
        headers=second_verified_tenant["headers"],
    )
    staff_delete = client.delete(
        f"/api/v1/staff/{tenant_a_staff['teacher_id']}",
        headers=second_verified_tenant["headers"],
    )

    assert group_get.status_code == status.HTTP_404_NOT_FOUND
    assert group_update.status_code == status.HTTP_404_NOT_FOUND
    assert child_get.status_code == status.HTTP_403_FORBIDDEN
    assert child_update.status_code == status.HTTP_403_FORBIDDEN
    assert staff_get.status_code == status.HTTP_403_FORBIDDEN
    assert staff_delete.status_code == status.HTTP_403_FORBIDDEN


def test_list_endpoints_only_expose_current_tenant_data(
    client,
    verified_tenant,
    second_verified_tenant,
    create_group,
    create_child,
    create_staff,
):
    tenant_a_group = create_group(verified_tenant, name="Tenant A Group")
    tenant_b_group = create_group(second_verified_tenant, name="Tenant B Group")
    create_child(verified_tenant, tenant_a_group["group_id"], full_name="Tenant A Child")
    create_child(second_verified_tenant, tenant_b_group["group_id"], full_name="Tenant B Child")
    create_staff(verified_tenant, group_id=tenant_a_group["group_id"], full_name="Tenant A Staff")
    create_staff(second_verified_tenant, group_id=tenant_b_group["group_id"], full_name="Tenant B Staff")

    groups_response = client.get("/api/v1/groups/", headers=verified_tenant["headers"])
    children_response = client.get("/api/v1/children/", headers=verified_tenant["headers"])
    staff_response = client.get("/api/v1/staff/", headers=verified_tenant["headers"])

    assert groups_response.status_code == status.HTTP_200_OK
    assert children_response.status_code == status.HTTP_200_OK
    assert staff_response.status_code == status.HTTP_200_OK

    assert groups_response.json()["total"] == 1
    assert children_response.json()["total"] == 1
    assert staff_response.json()["total"] == 1
