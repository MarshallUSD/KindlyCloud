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
    assert response.status_code == status.HTTP_400_BAD_REQUEST
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


def test_staff_crud_filter_and_search(client, test_kindergarten_user_token, test_group):
    create_response = client.post(
        "/api/v1/staff/",
        json={
            "full_name": "Nargiza Xasanova",
            "phone": "+998901999888",
            "role": "teacher",
            "salary": "4500000",
            "hired_at": "2025-09-01",
            "group_id": test_group.group_id,
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    staff_member = create_response.json()
    assert staff_member["group_id"] == test_group.group_id
    assert staff_member["role"] == "teacher"

    list_response = client.get(
        f"/api/v1/staff/?group_id={test_group.group_id}&search=Nargiza",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert list_response.status_code == status.HTTP_200_OK
    data = list_response.json()
    assert data["total"] >= 1
    assert all(item["group_id"] == test_group.group_id for item in data["items"])
    assert any(item["full_name"] == "Nargiza Xasanova" for item in data["items"])

    update_response = client.put(
        f"/api/v1/staff/{staff_member['teacher_id']}",
        json={"role": "assistant", "group_id": None},
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["role"] == "assistant"
    assert update_response.json()["group_id"] is None

    delete_response = client.delete(
        f"/api/v1/staff/{staff_member['teacher_id']}",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


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
    assert teacher["role"] == "teacher"

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


def test_children_and_staff_cross_tenant_access_return_403(
    client, db_session, test_group, test_child, test_pedagogue
):
    from app.core.security import create_access_token, get_password_hash
    from app.models.kindergarten import Kindergarten, KindergartenUser
    from app.models.user import User, UserRole

    other_user = User(
        full_name="Other Kindergarten",
        phone_or_email="other-m3@test.com",
        role=UserRole.KINDERGARTEN,
        password_hash=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(other_user)
    db_session.flush()

    other_kindergarten = Kindergarten(
        kindergarten_id=str(uuid.uuid4()),
        kinder_name="Other Milestone 3 Tenant",
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
    headers = {"Authorization": f"Bearer {token}"}

    child_response = client.get(f"/api/v1/children/{test_child.child_id}", headers=headers)
    assert child_response.status_code == status.HTTP_403_FORBIDDEN

    staff_response = client.get(f"/api/v1/staff/{test_pedagogue.teacher_id}", headers=headers)
    assert staff_response.status_code == status.HTTP_403_FORBIDDEN


def test_child_search_and_foreign_group_validation(client, db_session, test_kindergarten_user_token, test_group):
    from app.models.kindergarten import Kindergarten
    from app.models.group import Group
    from datetime import date

    response = client.post(
        "/api/v1/children/",
        json={
            "full_name": "Kamila Ergasheva",
            "birth_date": "2021-02-10",
            "gender": "female",
            "parent_phone": "+998900000099",
            "group_id": test_group.group_id,
            "notes": "Allergy: peanuts",
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["notes"] == "Allergy: peanuts"

    search_response = client.get(
        "/api/v1/children/?search=Kamila",
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert search_response.status_code == status.HTTP_200_OK
    assert any(item["full_name"] == "Kamila Ergasheva" for item in search_response.json()["items"])

    foreign_kindergarten = Kindergarten(
        kindergarten_id=str(uuid.uuid4()),
        kinder_name="Foreign Kindergarten",
        is_verified=True,
    )
    db_session.add(foreign_kindergarten)
    db_session.flush()

    foreign_group = Group(
        group_id=str(uuid.uuid4()),
        kindergarten_id=foreign_kindergarten.kindergarten_id,
        group_name="Foreign Group",
        start_date=date(2026, 1, 1),
        max_capacity=10,
    )
    db_session.add(foreign_group)
    db_session.commit()

    foreign_group_response = client.post(
        "/api/v1/children/",
        json={
            "full_name": "Foreign Group Child",
            "birth_date": "2021-06-01",
            "parent_phone": "+998900000100",
            "group_id": foreign_group.group_id,
        },
        headers={"Authorization": f"Bearer {test_kindergarten_user_token}"},
    )
    assert foreign_group_response.status_code == status.HTTP_403_FORBIDDEN
