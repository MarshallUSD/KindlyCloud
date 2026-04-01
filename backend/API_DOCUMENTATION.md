# KindlyCloud - Kindergarten Management System API

## 📋 Overview

KindlyCloud is a comprehensive REST API for managing kindergarten operations including user authentication, enrollment, attendance tracking, payments, and more.

## 🚀 Features

- **Multi-role Authentication**: Admin, Kindergarten, and Parent users
- **Kindergarten Management**: Profiles, groups, and pedagogues
- **Child Management**: Registration, enrollment, and attendance tracking
- **Parent Portal**: Link children, view menus, make payments
- **Payment Processing**: Support for multiple payment providers
- **Feedback System**: Parent-teacher communication
- **Admin Dashboard**: Posts and system-wide management

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL with SQLAlchemy 2.0.25
- **Authentication**: JWT (PyJWT 2.8.0)
- **Password Hashing**: bcrypt
- **Migrations**: Alembic 1.13.1
- **Testing**: pytest 7.4.3

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL database

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd KindlyCloud
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables (create `.env` file):
```env
DEBUG=True
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API Documentation at `http://localhost:8000/docs`

## 🧪 Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_auth.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## 📚 API Endpoints

### Authentication & Admin (`/api/v1/auth`)

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "role": "parent|kindergarten|admin",
  "phone": "+998901234567",
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response**: `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "phone_or_email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Create Admin Post (Admin Only)
```http
POST /api/v1/auth/admin/posts
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Important Announcement",
  "body": "Details about the announcement",
  "target_kindergarten_id": "uuid" // optional
}
```

#### List Feedback (Admin Only)
```http
GET /api/v1/auth/admin/feedback?skip=0&limit=20&status_filter=pending
Authorization: Bearer <token>
```

### Kindergarten Routes (`/api/v1/kindergartens`)

All kindergarten endpoints require `kindergarten` role authentication.

#### Create Kindergarten Profile
```http
POST /api/v1/kindergartens/
Authorization: Bearer <token>
Content-Type: application/json

{
  "kinder_name": "Little Stars Kindergarten",
  "region": "Tashkent",
  "district": "Yunusabad",
  "address": "123 Main Street",
  "phone": "+998901234567",
  "email": "littlestars@example.com",
  "payment_note": "Monthly payment required"
}
```

#### Get My Kindergarten
```http
GET /api/v1/kindergartens/me
Authorization: Bearer <token>
```

#### Create Group
```http
POST /api/v1/kindergartens/groups
Authorization: Bearer <token>
Content-Type: application/json

{
  "group_name": "Rainbow Group",
  "teacher_id": "uuid",
  "start_date": "2026-03-01",
  "end_date": "2026-12-31",
  "schedule": "Monday-Friday 8:00-18:00",
  "max_capacity": 20
}
```

#### List Groups
```http
GET /api/v1/kindergartens/groups?skip=0&limit=20
Authorization: Bearer <token>
```

#### Create Child
```http
POST /api/v1/kindergartens/children
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "Ali",
  "last_name": "Karimov",
  "birth_date": "2021-05-15",
  "gender": "male",
  "address": "456 Park Avenue"
}
```

#### Create Enrollment
```http
POST /api/v1/kindergartens/enrollments
Authorization: Bearer <token>
Content-Type: application/json

{
  "child_id": "uuid",
  "group_id": "uuid",
  "enrol_date": "2026-03-10",
  "total_fees": "500000"
}
```

#### Mark Attendance
```http
POST /api/v1/kindergartens/attendance
Authorization: Bearer <token>
Content-Type: application/json

{
  "enrol_id": "uuid",
  "attend_date": "2026-03-10",
  "status": "present|absent|sick|excused",
  "notes": "Optional notes"
}
```

#### Create Menu
```http
POST /api/v1/kindergartens/menus
Authorization: Bearer <token>
Content-Type: application/json

{
  "menu_date": "2026-03-10",
  "items": [
    {
      "meal_type": "breakfast",
      "description": "Oatmeal with fruits"
    },
    {
      "meal_type": "lunch",
      "description": "Chicken soup with bread"
    }
  ],
  "group_ids": ["uuid1", "uuid2"]
}
```

### Parent Routes (`/api/v1/parent`)

All parent endpoints require `parent` role authentication.

#### Link Child to Parent
```http
POST /api/v1/parent/link-child
Authorization: Bearer <token>
Content-Type: application/json

{
  "child_id": "uuid",
  "note": "My son"
}
```

#### Get My Children
```http
GET /api/v1/parent/children
Authorization: Bearer <token>
```

#### Get Today's Menu
```http
GET /api/v1/parent/menus/today?child_id=uuid
Authorization: Bearer <token>
```

#### Create Payment
```http
POST /api/v1/parent/payments
Authorization: Bearer <token>
Content-Type: application/json

{
  "enrol_id": "uuid",
  "amount": "100000.00",
  "payment_date": "2026-03-10",
  "provider": "cash|stripe|paypal|bank_transfer",
  "transaction_id": "TXN123456"
}
```

#### List Payments
```http
GET /api/v1/parent/payments?skip=0&limit=20
Authorization: Bearer <token>
```

## 🔐 Authentication

All protected endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

Get a token by registering or logging in through the `/api/v1/auth/register` or `/api/v1/auth/login` endpoints.

## 📊 Database Schema

### User Roles

- **ADMIN**: System administrators with full access
- **KINDERGARTEN**: Kindergarten managers who can create groups, manage enrollments, etc.
- **PARENT**: Parents who can link children, view menus, and make payments

### Core Models

1. **User** - Base authentication model
2. **Kindergarten** - Kindergarten profiles
3. **Parent** - Parent profiles
4. **Child** - Child/student records
5. **Group** - Kindergarten groups/classes
6. **Pedagogue** - Teachers/educators
7. **Enrollment** - Child-Group relationships
8. **Attendance** - Daily attendance records
9. **Payment** - Payment transactions
10. **Menu** - Daily meal menus
11. **Post** - Admin announcements
12. **Feedback** - Parent-teacher communication

## 🔧 Configuration

Key configuration options in `config.py`:

```python
PROJECT_NAME = "KindlyCloud - Kindergarten Management System"
VERSION = "0.1.0"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
```

## 🧩 Project Structure

```
KindlyCloud/
├── app/
│   ├── api/
│   │   └── routes/          # API route handlers
│   ├── core/                # Core configurations
│   ├── models/              # SQLAlchemy models
│   ├── repositories/        # Data access layer
│   ├── schemas/             # Pydantic schemas
│   └── services/            # Business logic
├── tests/                   # Test suite
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## ✅ Testing Coverage

Current test coverage:
- ✅ Authentication (register, login, duplicate checking)
- ✅ Admin operations (posts, feedback)
- ✅ Kindergarten management (profiles, groups, children, enrollments)
- ✅ Parent operations (link children, payments, view menus)
- ✅ Authorization and access control

All 19 tests passing! 🎉

## 🚦 Status Codes

- `200 OK` - Successful GET/UPDATE requests
- `201 Created` - Successful POST requests
- `401 Unauthorized` - Invalid or missing authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource (e.g., email already exists)
- `422 Unprocessable Entity` - Validation errors

## 📝 Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {}
}
```

## 🌐 CORS Configuration

CORS is configured to allow all origins by default. For production, update `CORS_ORIGINS` in `config.py`:

```python
CORS_ORIGINS = ["https://yourdomain.com"]
```

## 🔄 Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## 🐛 Debugging

Enable debug mode in `.env`:
```env
DEBUG=True
```

This will:
- Show detailed error messages
- Enable auto-reload on code changes
- Display SQL queries (if `DATABASE_ECHO=True`)

## 📈 Future Enhancements

Potential areas for expansion:
- [ ] Email notifications
- [ ] SMS notifications for attendance
- [ ] File upload for child photos
- [ ] Reporting and analytics
- [ ] Mobile app integration
- [ ] Real-time notifications (WebSockets)
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 👥 Support

For support, contact: support@kindlycloud.com

---

**Made with ❤️ for better kindergarten management**
