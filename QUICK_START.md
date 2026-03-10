# KindlyCloud API - Quick Start Guide

## 🎯 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
uvicorn app.main:app --reload
```

### 3. Access the API
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Test the API

### Using the Interactive Docs (Recommended for Beginners)

1. Go to http://localhost:8000/docs
2. Try the `/health` endpoint (no auth required)
3. Register a user via `/api/v1/auth/register`
4. Copy the `access_token` from the response
5. Click the "Authorize" button at the top
6. Paste your token and click "Authorize"
7. Now you can test protected endpoints!

### Using cURL

#### 1. Register a Parent User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "parent",
    "phone": "+998901234567",
    "email": "parent@example.com",
    "password": "SecurePass123!"
  }'
```

#### 2. Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_or_email": "parent@example.com",
    "password": "SecurePass123!"
  }'
```

Save the `access_token` from the response.

#### 3. Use the Token
```bash
export TOKEN="your-access-token-here"

curl -X GET "http://localhost:8000/api/v1/parent/children" \
  -H "Authorization: Bearer $TOKEN"
```

## 🧪 Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with detailed output
pytest tests/ -v --tb=short

# Run and show print statements
pytest tests/ -v -s
```

All 19 tests should pass ✅

## 📊 User Workflows

### Parent Workflow

1. **Register** as a parent
2. **Login** to get access token
3. **Link your child** (child must be registered by kindergarten first)
4. **View children's information**
5. **Check today's menu** for your child's group
6. **Make payments** for enrollment fees
7. **View payment history**

### Kindergarten Workflow

1. **Register** as a kindergarten user
2. **Create kindergarten profile**
3. **Create groups** (classes)
4. **Register children**
5. **Enroll children** in groups
6. **Mark attendance** daily
7. **Create daily menus**

### Admin Workflow

1. **Login** as admin
2. **Create announcements/posts**
3. **View and manage feedback**
4. **Monitor system-wide activities**

## 🔑 Sample Data for Testing

### Admin User
```json
{
  "email": "admin@kindlycloud.com",
  "password": "Admin123!",
  "role": "admin"
}
```

### Kindergarten User
```json
{
  "email": "kinder@example.com",
  "password": "Kinder123!",
  "phone": "+998901234567",
  "role": "kindergarten"
}
```

### Parent User
```json
{
  "email": "parent@example.com",
  "password": "Parent123!",
  "phone": "+998901234568",
  "role": "parent"
}
```

## 📋 Common Operations

### Create a Complete Enrollment Flow

1. **Kindergarten creates a child**:
```bash
curl -X POST "http://localhost:8000/api/v1/kindergartens/children" \
  -H "Authorization: Bearer $KINDER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ali",
    "last_name": "Karimov",
    "birth_date": "2021-05-15",
    "gender": "male",
    "address": "123 Test St"
  }'
```

2. **Kindergarten enrolls child in a group**:
```bash
curl -X POST "http://localhost:8000/api/v1/kindergartens/enrollments" \
  -H "Authorization: Bearer $KINDER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child-uuid-from-step-1",
    "group_id": "group-uuid",
    "enrol_date": "2026-03-01",
    "total_fees": "500000"
  }'
```

3. **Parent links to child**:
```bash
curl -X POST "http://localhost:8000/api/v1/parent/link-child" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child-uuid-from-step-1",
    "note": "My son"
  }'
```

4. **Parent makes payment**:
```bash
curl -X POST "http://localhost:8000/api/v1/parent/payments" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enrol_id": "enrollment-uuid-from-step-2",
    "amount": "100000.00",
    "payment_date": "2026-03-10",
    "provider": "cash",
    "transaction_id": "TXN001"
  }'
```

## ⚠️ Common Issues & Solutions

### Issue: "Module not found"
**Solution**: Make sure you're in the project directory and have activated your virtual environment.

### Issue: "Database connection error"
**Solution**: Check your `DATABASE_URL` in config.py or .env file.

### Issue: "401 Unauthorized"
**Solution**: 
1. Make sure you've included the `Authorization: Bearer <token>` header
2. Check that your token hasn't expired
3. Verify you're using the correct role for the endpoint

### Issue: "403 Forbidden"
**Solution**: You're authenticated but don't have the right permissions. Check the required role for the endpoint.

### Issue: Tests failing
**Solution**: 
1. Make sure all dependencies are installed
2. Delete `test.db` if it exists
3. Run `pytest tests/ -v` again

## 🎓 Learning Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Tutorial**: https://docs.sqlalchemy.org/en/20/tutorial/
- **Pydantic Guide**: https://docs.pydantic.dev/
- **JWT Introduction**: https://jwt.io/introduction

## 🔧 Development Tips

1. **Use the Interactive Docs** at `/docs` - it's the easiest way to explore the API
2. **Check test files** in `tests/` for usage examples
3. **Enable DEBUG mode** during development for better error messages
4. **Use Alembic** for database schema changes
5. **Write tests** for new features before implementing them

## 📞 Need Help?

1. Check the full **API_DOCUMENTATION.md** for detailed endpoint information
2. Review the **test files** for code examples
3. Use the **Interactive API docs** at `/docs`
4. Check **error messages** - they're designed to be helpful!

---

**Happy Coding! 🚀**

For production deployment, remember to:
- Change the `SECRET_KEY`
- Set `DEBUG=False`
- Configure proper CORS origins
- Use a production database
- Set up proper logging
- Enable HTTPS
