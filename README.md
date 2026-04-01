# KindlyCloud

KindlyCloud is a FastAPI backend for a multi-tenant kindergarten management platform. It supports JWT authentication, role-based access control, kindergarten verification, and tenant-safe operational APIs for groups, children, staff (pedagogues), parents, enrollments, attendance, menus, notifications, and payments.

Milestone 6 Part 1 is now implemented:

- parents now have a tenant-safe read layer for dashboard, attendance, menu, and notifications
- `GET /api/v1/parent/dashboard` aggregates linked child, group, pedagogue, today attendance, published menu, latest payment, and unread notification count
- `GET /api/v1/parent/attendance` supports exact-date and date-range history for linked children only
- `GET /api/v1/parent/menu` returns the published menu for a linked child's group and defaults to today
- `GET /api/v1/parent/notifications` and `PATCH /api/v1/parent/notifications/{notification_id}/read` provide parent-scoped notification reads
- menus now support `draft` and `published` status with `published_at`, while the legacy `GET /api/v1/parent/menus/today` route remains available
- parent profiles are ready for future Telegram linkage through optional `telegram_id`

Milestone 5 remains implemented:

- kindergarten users create and manage tenant-scoped monthly payment records
- payment status is limited to `pending`, `paid`, and `overdue`
- overdue status is enforced automatically from `due_date`
- parents can only read payments for linked children
- payment events write notification-ready records to the existing `notifications` table
- kindergarten users can export payment PDF reports for daily, weekly, monthly, and custom ranges

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

Milestone 6 Part 1 parent read layer:

- parent dashboard returns linked children only and never leaks foreign children or foreign tenant data
- dashboard attendance uses explicit `unmarked` when today's attendance is missing
- parent menu reads only published menus; draft menus stay hidden from parents
- parent attendance defaults to the last 30 days when no filters are supplied
- parent notifications are user-scoped and expose `is_read` plus `read_at`
- menu creation now rejects duplicate menus for the same group and date at the service layer

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
- payment records enforce tenant-safe child ownership and one record per child plus billing period inside each tenant

## Core Models

Key auth and tenant models:

- `users`
- `kindergartens`
- `kindergarten_users`
- `parents`
- `parent_users`

Parent identity model:

- `parents` stores the real-world guardian profile
- `parent_users` stores the authenticated access link for that guardian
- one `parent_user` links to one `parent`
- one `parent` can be linked to multiple children through `parent_child_links`
- optional `telegram_id` is stored on `parents` for future bot integration

Operational models:

- `groups`
- `children`
- `pedagogues` for staff and teachers
- `enrollments`
- `attendance`
- `menus`
- `notifications`
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
- `GET /api/v1/parent/dashboard`
- `GET /api/v1/parent/attendance`
- `GET /api/v1/parent/menu`
- `GET /api/v1/parent/menus/today`
- `GET /api/v1/parent/notifications`
- `PATCH /api/v1/parent/notifications/{notification_id}/read`
- `GET /api/v1/parent/payments`
- `GET /api/v1/parent/payments/{payment_id}`

Parent read notes:

- `GET /api/v1/parent/menu` requires `child_id` when the parent has multiple linked children
- `GET /api/v1/parent/menu` defaults `date` to today when omitted
- `GET /api/v1/parent/attendance` accepts `child_id`, `date`, `date_from`, and `date_to`
- `date` cannot be combined with `date_from` or `date_to`
- if no attendance filters are provided, the API returns the last 30 days for linked children
- `/api/v1/parent/menus/today` is kept for backward compatibility and returns today's published menu only

Menu behavior:

- menus are date-based records assigned to groups
- parent reads only published menus
- kindergarten menu creation accepts `status` with `published` as the default for backward compatibility
- duplicate menus for the same group and date are rejected

### Payments

- `POST /api/v1/payments/`
- `GET /api/v1/payments/`
- `GET /api/v1/payments/{payment_id}`
- `PATCH /api/v1/payments/{payment_id}`
- `PATCH /api/v1/payments/{payment_id}/mark-paid`

### Reports

- `GET /api/v1/reports/payments/export?period=daily`
- `GET /api/v1/reports/payments/export?period=weekly`
- `GET /api/v1/reports/payments/export?period=monthly`
- `GET /api/v1/reports/payments/export?period=custom&from_date=2026-04-01&to_date=2026-04-30`

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

Milestone 5 examples:

Create a payment record:

```http
POST /api/v1/payments/
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "child_id": "<child_uuid>",
  "amount": "500000.00",
  "due_date": "2026-04-10",
  "billing_period": "2026-04",
  "status": "pending",
  "notes": "April tuition"
}
```

Mark a payment as paid:

```http
PATCH /api/v1/payments/<payment_uuid>/mark-paid
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "payment_method": "cash"
}
```

Export the monthly payment report:

```http
GET /api/v1/reports/payments/export?period=monthly
Authorization: Bearer <jwt>
```

Milestone 6 Part 1 examples:

Parent dashboard:

```http
GET /api/v1/parent/dashboard
Authorization: Bearer <parent_jwt>
```

Parent attendance history:

```http
GET /api/v1/parent/attendance?child_id=<child_uuid>&date_from=2026-03-01&date_to=2026-03-31
Authorization: Bearer <parent_jwt>
```

Parent menu:

```http
GET /api/v1/parent/menu?child_id=<child_uuid>&date=2026-04-01
Authorization: Bearer <parent_jwt>
```

Parent notifications:

```http
GET /api/v1/parent/notifications?skip=0&limit=20
Authorization: Bearer <parent_jwt>
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
- added Milestone 5 payment tracking/reporting migration `20260331_0005_milestone5_payments.py`
- payments now use tenant-scoped monthly billing records, notification hooks, and PDF export support
- added Milestone 6 parent read layer migration `20260401_0006_milestone6_parent_read_layer.py`
- migration `20260401_0006_milestone6_parent_read_layer.py` adds optional `parents.telegram_id`, menu publish fields, and a uniqueness guard for duplicate group-menu assignments
- after applying the migration, existing menus are backfilled as `published` with `published_at` derived from `created_at`

## Notes

This README reflects the current backend behavior in code. If older notes or external docs conflict with the implemented API, the code and test suite should be treated as the source of truth.
