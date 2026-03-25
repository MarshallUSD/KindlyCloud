"""Milestone 2 CRUD and tenant isolation tests."""
import uuid

from fastapi import status


def test_groups_crud_flow(client, test_kindergarten_user_token, test_kindergarten, test_pedagogue):
    create_response = client.post(
        "/api/v1/groups/",
        json={
            "name": "Tulip Group",
            "age_from": 4,
            "age_to": 6,
            "capacity": 15,
            "schedule_from": "08:30:00",
            "schedule_to": "17:30:00",
            "monthly_fee": "650000",
            "teacher_id": test_pedagogue.teacher_id,
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    group = create_response.json()
    assert group["kindergarten_id"] == test_kindergarten.kindergarten_id

    list_response = client.get(
        "/api/v1/groups/",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.json()["total"] >= 1

    update_response = client.put(
        f"/api/v1/groups/{group['group_id']}",
        json={"capacity": 18},
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["capacity"] == 18


def test_children_capacity_validation(client, test_kindergarten_user_token, test_group, db_session):
    from app.models.child import Child
    from datetime import date

    test_group.max_capacity = 1
    db_session.add(test_group)
    db_session.add(
        Child(
            child_id=str(uuid.uuid4()),
            kindergarten_id=test_group.kindergarten_id,
            group_id=test_group.group_id,
            full_name="Existing Child",
            parent_phone="+998900000001",
            first_name="Existing",
            last_name="Child",
            birth_date=date(2021, 1, 1),
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/children/",
        json={
            "full_name": "Second Child",
            "birth_date": "2021-05-15",
            "parent_phone": "+998900000002",
            "group_id": test_group.group_id,
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"] == "Group capacity has been reached"


def test_children_group_filter(client, test_kindergarten_user_token, test_child):
    response = client.get(
        f"/api/v1/children/?group_id={test_child.group_id}",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert all(item["group_id"] == test_child.group_id for item in data["items"])


def test_teachers_crud_and_filter(client, test_kindergarten_user_token, test_group):
    create_response = client.post(
        "/api/v1/teachers/",
        json={
            "full_name": "Nargiza Xasanova",
            "phone": "+998901999888",
            "experience_year": 4,
            "group_id": test_group.group_id,
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    teacher = create_response.json()
    assert teacher["group_id"] == test_group.group_id
    assert teacher["experience_year"] == 4

    list_response = client.get(
        f"/api/v1/teachers/?group_id={test_group.group_id}",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert list_response.status_code == status.HTTP_200_OK
    data = list_response.json()
    assert data["total"] >= 1
    assert all(item["group_id"] == test_group.group_id for item in data["items"])

    delete_response = client.delete(
        f"/api/v1/teachers/{teacher['teacher_id']}",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


def test_cross_tenant_access_is_blocked(client, db_session, test_group):
    from app.core.security import create_access_token, get_password_hash
    from app.models.kindergarten import Kindergarten, KindergartenUser
    from app.models.user import User, UserRole

    other_user = User(
        full_name="Other Kindergarten",
        phone_or_email="other-kinder@test.com",
        role=UserRole.KINDERGARTEN,
        password_hash=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(other_user)
    db_session.flush()

    other_kindergarten = Kindergarten(
        kindergarten_id=str(uuid.uuid4()),
        kinder_name="Other Tenant",
        is_verified=True,
    )
    db_session.add(other_kindergarten)
    db_session.flush()

    db_session.add(
        KindergartenUser(
            kindergarten_user_id=str(uuid.uuid4()),
            user_id=other_user.user_id,
            kindergarten_id=other_kindergarten.kindergarten_id,
        )
    )
    db_session.commit()

    token = create_access_token(data={"sub": str(other_user.user_id), "role": other_user.role})
    response = client.get(
        f"/api/v1/groups/{test_group.group_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
