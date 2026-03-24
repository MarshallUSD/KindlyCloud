# KindlyCloud

KindlyCloud is a FastAPI backend for a role-based kindergarten management platform. It provides authentication, tenant-aware kindergarten operations, parent access, and internal admin controls.

## Stack

- FastAPI
- SQLAlchemy
- JWT authentication
- PostgreSQL in app design
- SQLite used in tests

## Roles

The backend supports three roles:

- `admin`
- `kindergarten`
- `parent`

Authentication identifies the current user from a bearer token. Authorization is then enforced with route dependencies based on role and, for kindergarten users, verification status.

## Authentication And Authorization

### Shared authentication

`get_current_user` in [app/core/dependencies.py](/d:/Documents2/KindlyCloud/app/core/dependencies.py) decodes the JWT, checks it is an access token, loads the user from the database, and blocks inactive users.

### Kindergarten authorization

- `get_current_kindergarten_user`: requires an authenticated user with `role=kindergarten`
- `get_verified_kindergarten_user`: requires `role=kindergarten` and a linked kindergarten with `is_verified=True`

If a kindergarten account is not yet verified, protected operational routes return:

`403 Forbidden`

`"Kindergarten account is pending verification"`

### Parent authorization

`get_current_parent_user` requires an authenticated user with `role=parent`.

### Admin authorization

`get_current_admin` requires an admin token and an active admin record.

## Real Backend Behavior

This README reflects the current codebase behavior:

- Kindergarten users register with email and password
- Kindergarten users log in with email and password
- Parent users log in with phone number and password
- Admin users log in with email and password
- Kindergarten verification is enforced in backend authorization, not by frontend-only checks
- Admin verifies kindergartens through an admin endpoint

Not currently implemented in backend code:

- OTP login flow
- automatic verification emails
- multiple kindergartens per one business owner account

## Main Routes

### Auth

- `POST /api/v1/auth/register` - register a kindergarten-side user
- `POST /api/v1/auth/login` - kindergarten login
- `POST /api/v1/auth/parent-login` - parent login
- `POST /api/v1/auth/refresh` - refresh token
- `POST /api/v1/auth/logout` - logout
- `GET /api/v1/auth/me` - return current authenticated subject

### Kindergarten

Allowed for authenticated kindergarten users:

- `POST /api/v1/kindergartens/` - create kindergarten profile
- `GET /api/v1/kindergartens/me` - get own kindergarten profile

Allowed only for verified kindergarten users:

- `POST /api/v1/kindergartens/groups`
- `GET /api/v1/kindergartens/groups`
- `POST /api/v1/kindergartens/children`
- `POST /api/v1/kindergartens/parents`
- `POST /api/v1/kindergartens/enrollments`
- `POST /api/v1/kindergartens/attendance`
- `POST /api/v1/kindergartens/menus`

### Parent

- `GET /api/v1/parent/children`
- `GET /api/v1/parent/menus/today`
- `POST /api/v1/parent/payments`
- `GET /api/v1/parent/payments`

### Admin

- `POST /api/v1/admin/auth/login`
- `POST /api/v1/admin/posts`
- `GET /api/v1/admin/feedback`
- `PATCH /api/v1/admin/feedback/{feedback_id}`
- `POST /api/v1/admin/verify-kindergarten/{user_id}`

## Data Model Summary

Core auth and tenant relationships:

- `users`: central authentication records with a `role`
- `kindergartens`: kindergarten business profile with `is_verified`
- `kindergarten_users`: links a user to a kindergarten
- `parents`: parent profile
- `parent_users`: links a user to a parent profile

Operational entities include:

- `groups`
- `children`
- `enrollments`
- `attendance`
- `menus`
- `payments`
- `feedback`
- `posts`

## Verification Rules

Kindergarten verification is enforced like this:

1. A kindergarten user can register and log in before verification.
2. An unverified kindergarten user can access `/api/v1/auth/me`.
3. An unverified kindergarten user can access `/api/v1/kindergartens/me`.
4. An unverified kindergarten user cannot access operational kindergarten endpoints.
5. An admin can verify the kindergarten through `/api/v1/admin/verify-kindergarten/{user_id}`.
6. After verification, normal kindergarten operational access is allowed.

## Running Tests

From the project root:

```powershell
venv\Scripts\pytest.exe
```

The verification behavior is covered by tests in:

- [tests/test_auth.py](/d:/Documents2/KindlyCloud/tests/test_auth.py)
- [tests/test_kindergarten.py](/d:/Documents2/KindlyCloud/tests/test_kindergarten.py)
- [tests/test_admin.py](/d:/Documents2/KindlyCloud/tests/test_admin.py)

## Project Status

Backend MVP is in active development. The implemented behavior should be treated as the source of truth over older documentation.
