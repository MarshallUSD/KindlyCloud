# Milestone 2 API Examples

Base URL: `http://localhost:8000/api/v1`

Headers:

```http
Authorization: Bearer <KINDERGARTEN_JWT>
Content-Type: application/json
```

## Groups

### Create Group

```http
POST /groups
```

```json
{
  "name": "Rainbow Group",
  "age_from": 3,
  "age_to": 5,
  "capacity": 20,
  "schedule_from": "08:00:00",
  "schedule_to": "18:00:00",
  "monthly_fee": "500000",
  "teacher_id": "teacher-uuid"
}
```

### List Groups

```http
GET /groups?skip=0&limit=20
```

### Get Group By ID

```http
GET /groups/{group_id}
```

### Update Group

```http
PUT /groups/{group_id}
```

```json
{
  "capacity": 25,
  "monthly_fee": "550000"
}
```

### Delete Group

```http
DELETE /groups/{group_id}
```

## Children

### Create Child

```http
POST /children
```

```json
{
  "full_name": "Ali Karimov",
  "birth_date": "2021-05-15",
  "parent_phone": "+998901234567",
  "group_id": "group-uuid"
}
```

### List Children

```http
GET /children?skip=0&limit=20&group_id=group-uuid
```

### Get Child By ID

```http
GET /children/{child_id}
```

### Update Child

```http
PUT /children/{child_id}
```

```json
{
  "group_id": "new-group-uuid",
  "parent_phone": "+998901000111"
}
```

### Delete Child

```http
DELETE /children/{child_id}
```

## Teachers

### Create Teacher

```http
POST /teachers
```

```json
{
  "full_name": "Nargiza Xasanova",
  "phone": "+998901999888",
  "experience_year": 4,
  "group_id": "group-uuid"
}
```

### List Teachers

```http
GET /teachers?skip=0&limit=20&group_id=group-uuid
```

### Get Teacher By ID

```http
GET /teachers/{teacher_id}
```

### Update Teacher

```http
PUT /teachers/{teacher_id}
```

```json
{
  "phone": "+998901112233",
  "experience_year": 5,
  "group_id": "other-group-uuid"
}
```

### Delete Teacher

```http
DELETE /teachers/{teacher_id}
```
