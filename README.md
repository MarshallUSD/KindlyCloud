# KindlyCloud

KindlyCloud is a FastAPI backend for a multi-tenant kindergarten management platform. It supports JWT authentication, role-based access control, kindergarten verification, and tenant-safe operational APIs for groups, children, staff (pedagogues), parents, enrollments, attendance, menus, and payments.

## Current Scope

Milestone 1 is completed:

- JWT authentication
- Roles: `admin`, `kindergarten`, `parent`
- Only kindergarten users can access the main operational system

Milestone 2 is completed:

- Multi-tenant isolation by `kindergarten_id`
- CRUD for groups, children, and teachers
- Pagination on list endpoints
- Filtering by `group_id`
- Group capacity validation
- Same-tenant validation for child, teacher, and group relationships
- Automatic tenant assignment from the authenticated kindergarten user

Milestone 3 is now implemented:

- Children CRUD uses the Milestone 3 contract with `full_name`, `birth_date`, `gender`, `group_id`, `parent_phone`, and optional `notes`
- Staff CRUD is available via `/api/v1/staff/`
- Staff records are tenant-scoped pedagogues with `full_name`, `phone`, `role`, optional `salary`, optional `hired_at`, and optional `group_id`
- Children must always be created inside a group owned by the same kindergarten
- Staff can be created first and then assigned to a group, or assigned during create/update
- List endpoints support pagination and basic name search
- Cross-tenant child and staff access now returns `403 Forbidden`

Milestone 4 is now implemented:

- Daily attendance is managed by group and date
- Bulk attendance upsert is available via `/api/v1/attendance/bulk`
- Daily attendance view returns all children in a group even before attendance is marked
- Attendance history supports tenant-safe date range and optional group filtering
- Attendance summary returns `total_children`, `present_count`, `late_count`, `absent_count`, and `unmarked_count`
- Attendance status supports only `present`, `late`, and `absent`
- Attendance enforces one record per child per date
- Attendance validation blocks cross-tenant access and rejects children outside the selected group

## Stack

- FastAPI
- SQLAlchemy
- Pydantic v2
- JWT authentication
- Alembic
- PostgreSQL-oriented backend design
- SQLite used in tests

## Architecture

The backend follows a layered structure:

- `app/api/routes/` for FastAPI routers
- `app/services/` for business logic
- `app/models/` for SQLAlchemy models
- `app/schemas/` for request and response models
- `app/core/` for config, auth, dependencies, exceptions, and DB setup

## Roles And Access

The platform supports three roles:

- `admin`
- `kindergarten`
- `parent`

Authorization is enforced through dependencies in [app/core/dependencies.py](d:/Documents2/KindlyCloud/app/core/dependencies.py).

### Kindergarten access

- `get_current_kindergarten_user` requires an authenticated kindergarten user
- `get_verified_kindergarten_user` requires a kindergarten user linked to a verified kindergarten

If a kindergarten is not verified, operational routes return:

- `403 Forbidden`
- `"Kindergarten account is pending verification"`

### Parent access

- `get_current_parent_user` requires an authenticated parent user

### Admin access

- `get_current_admin` requires a valid admin token and active admin record

## Multi-Tenant Rules

Each kindergarten is a separate tenant.

All operational entities are scoped by `kindergarten_id`, and the backend enforces strict tenant isolation:

- clients cannot submit `kindergarten_id`
- the backend derives `kindergarten_id` from the current authenticated kindergarten user
- kindergarten users can only read and mutate their own tenant data
- linked entities such as `group_id` and `teacher_id` must belong to the same tenant
- child creation and reassignment respect group capacity
- child and staff queries distinguish `404 not found` from `403 foreign-tenant access`
- attendance validates that the group belongs to the current tenant
- attendance validates that every child belongs to the current tenant and the selected group
- attendance upserts by child and date to avoid duplicates

## Core Models

Key auth and tenant models:

- `users`
- `kindergartens`
- `kindergarten_users`
- `parents`
- `parent_users`

Operational models:

- `groups`
- `children`
- `pedagogues` for staff and teachers
- `enrollments`
- `attendance`
- `menus`
- `payments`
- `feedback`
- `posts`

Staff records currently support:

- `full_name`
- `phone`
- `role`
- optional `salary`
- optional `hired_at`
- optional `group_id`
- `kindergarten_id`

## Main Routes

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/parent-login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Admin

- `POST /api/v1/admin/auth/login`
- `POST /api/v1/admin/posts`
- `GET /api/v1/admin/feedback`
- `PATCH /api/v1/admin/feedback/{feedback_id}`
- `POST /api/v1/admin/verify-kindergarten/{user_id}`

### Kindergarten Profile

- `POST /api/v1/kindergartens/`
- `GET /api/v1/kindergartens/me`

### Milestone 3 CRUD

These endpoints require an authenticated kindergarten user.

Groups:

- `POST /api/v1/groups/`
- `GET /api/v1/groups/`
- `GET /api/v1/groups/{group_id}`
- `PUT /api/v1/groups/{group_id}`
- `DELETE /api/v1/groups/{group_id}`

Children:

- `POST /api/v1/children/`
- `GET /api/v1/children/`
- `GET /api/v1/children/{child_id}`
- `PUT /api/v1/children/{child_id}`
- `DELETE /api/v1/children/{child_id}`

Staff:

- `POST /api/v1/staff/`
- `GET /api/v1/staff/`
- `GET /api/v1/staff/{staff_id}`
- `PUT /api/v1/staff/{staff_id}`
- `DELETE /api/v1/staff/{staff_id}`

Teachers compatibility route:

- `POST /api/v1/teachers/`
- `GET /api/v1/teachers/`
- `GET /api/v1/teachers/{teacher_id}`
- `PUT /api/v1/teachers/{teacher_id}`
- `DELETE /api/v1/teachers/{teacher_id}`

Filters and pagination:

- `skip` and `limit` are supported on list endpoints
- `group_id` filtering is supported on `/children/`, `/staff/`, and `/teachers/`
- `search` is supported on `/children/`, `/staff/`, and `/teachers/`
- service-level validation errors return `400 Bad Request`

### Other Kindergarten Operations

- `POST /api/v1/kindergartens/groups`
- `GET /api/v1/kindergartens/groups`
- `POST /api/v1/kindergartens/children`
- `POST /api/v1/kindergartens/parents`
- `POST /api/v1/kindergartens/enrollments`
- `POST /api/v1/kindergartens/attendance`
- `POST /api/v1/kindergartens/menus`

### Attendance

These endpoints require a verified kindergarten user.

- `POST /api/v1/attendance/bulk`
- `GET /api/v1/attendance/daily`
- `GET /api/v1/attendance/history`
- `GET /api/v1/attendance/summary`

Notes:

- `POST /api/v1/kindergartens/attendance` remains available as a legacy compatibility route
- the main Milestone 4 attendance flow now lives under `/api/v1/attendance/`

### Parent

- `GET /api/v1/parent/children`
- `GET /api/v1/parent/menus/today`
- `POST /api/v1/parent/payments`
- `GET /api/v1/parent/payments`

## Running Locally

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Useful URLs:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Running Tests

From the project root:

```powershell
venv\Scripts\pytest.exe -q
```

Current verified status depends on the latest local test run.

Relevant test files:

- [tests/test_auth.py](d:/Documents2/KindlyCloud/tests/test_auth.py)
- [tests/test_admin.py](d:/Documents2/KindlyCloud/tests/test_admin.py)
- [tests/test_kindergarten.py](d:/Documents2/KindlyCloud/tests/test_kindergarten.py)
- [tests/test_parent.py](d:/Documents2/KindlyCloud/tests/test_parent.py)
- [tests/test_milestone2.py](d:/Documents2/KindlyCloud/tests/test_milestone2.py)
- [tests/test_attendance.py](d:/Documents2/KindlyCloud/tests/test_attendance.py)

## Example Requests

Milestone 2 request examples are documented in:

- [API_MILESTONE2_EXAMPLES.md](d:/Documents2/KindlyCloud/API_MILESTONE2_EXAMPLES.md)

Milestone 3 examples:

Create a child:

```http
POST /api/v1/children/
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "full_name": "Kamila Ergasheva",
  "birth_date": "2021-02-10",
  "gender": "female",
  "group_id": "<group_uuid>",
  "parent_phone": "+998900000099",
  "notes": "Allergy: peanuts"
}
```

Create a staff member:

```http
POST /api/v1/staff/
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "full_name": "Nargiza Xasanova",
  "phone": "+998901999888",
  "role": "teacher",
  "salary": "4500000",
  "hired_at": "2025-09-01",
  "group_id": "<group_uuid>"
}
```

Search staff:

```http
GET /api/v1/staff/?search=Nargiza&skip=0&limit=20
Authorization: Bearer <jwt>
```

Milestone 4 examples:

Bulk save attendance:

```http
POST /api/v1/attendance/bulk
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "group_id": "<group_uuid>",
  "date": "2026-03-30",
  "records": [
    {"child_id": "<child_1_uuid>", "status": "present"},
    {"child_id": "<child_2_uuid>", "status": "late"},
    {"child_id": "<child_3_uuid>", "status": "absent"}
  ]
}
```

Daily attendance view:

```http
GET /api/v1/attendance/daily?group_id=<group_uuid>&date=2026-03-30
Authorization: Bearer <jwt>
```

Attendance history:

```http
GET /api/v1/attendance/history?group_id=<group_uuid>&date_from=2026-03-01&date_to=2026-03-30
Authorization: Bearer <jwt>
```

Attendance summary:

```http
GET /api/v1/attendance/summary?group_id=<group_uuid>&date=2026-03-30
Authorization: Bearer <jwt>
```

## Migrations

Alembic migrations live in `alembic/versions/`.

Recent schema changes:

- added Milestone 3 `children.notes`
- added Milestone 3 `pedagogues.role`
- added Milestone 3 `pedagogues.salary`
- added Milestone 3 `pedagogues.hired_at`
- added Milestone 4 attendance upgrade migration `20260330_0004_milestone4_attendance.py`
- attendance now includes tenant and group scoping, daily uniqueness per child, and summary-friendly indexes

## Notes

This README reflects the current backend behavior in code. If older notes or external docs conflict with the implemented API, the code and test suite should be treated as the source of truth.
