# KindlyCloud backend — Linux'da ishga tushirish qo'llanmasi

Loyihadagi `venv/` papkasi Windows'da yaratilgan (`venv/Scripts`, `venv/Lib`) va
Linux'da ishlamaydi. Quyida Linux uchun to'liq, noldan ishga tushirish tartibi.

Hamma buyruqlar `backend/` papkasi ichidan bajariladi:

```bash
cd ~/Work/KindlyCloud/backend
```

---

## 1. Virtual muhit va kutubxonalar

Tizimda `pip` bo'lmasa, avval uni bootstrap qilamiz:

```bash
python3 -m venv --without-pip .venv-linux
curl -sS -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
.venv-linux/bin/python /tmp/get-pip.py
```

`python3-venv` va `python3-pip` allaqachon o'rnatilgan tizimda oddiygina:

```bash
python3 -m venv .venv-linux
```

So'ng kutubxonalar:

```bash
.venv-linux/bin/pip install -r requirements.txt
```

---

## 2. Ma'lumotlar bazasi (PostgreSQL)

`.env.example` dagi Render'dagi masofaviy baza **o'chib ketgan** (free tier muddati
tugagan — TCP ulanadi, lekin SSL darhol uziladi). Shuning uchun lokal PostgreSQL
ishlatamiz:

```bash
docker run -d --name kindlycloud-db \
  -e POSTGRES_USER=kindergarten \
  -e POSTGRES_PASSWORD=kindlycloud \
  -e POSTGRES_DB=kindlycloud \
  -p 127.0.0.1:5436:5432 \
  postgres:16-alpine
```

Tayyorligini tekshirish:

```bash
docker exec kindlycloud-db pg_isready -U kindergarten
```

`.env` faylida shu baza ko'rsatilgan:

```
DATABASE_URL=postgresql://kindergarten:kindlycloud@localhost:5436/kindlycloud
```

> Eski Render sozlamasi `.env.render-backup` faylida saqlab qo'yilgan.

---

## 3. Sxemani yaratish

```bash
.venv-linux/bin/python scripts/init_db.py
```

Bu 25 ta jadvalni yaratadi va Alembic'ni `head`ga stamp qiladi.
Bazani butunlay tozalab qayta yaratish uchun: `scripts/init_db.py --drop`.

### Nega to'g'ridan-to'g'ri `alembic upgrade head` emas?

`alembic/versions/` dagi migratsiyalar **inkremental**: birinchi migratsiya
(`20260319_0001`) allaqachon mavjud `posts`, `users`, `kindergartens` jadvallariga
`ALTER TABLE` qiladi. Ya'ni bazaviy sxema hech qachon migratsiyaga yozilmagan.
Bo'sh bazada `alembic upgrade head` shu sababli quyidagi xato bilan yiqiladi:

```
psycopg2.errors.UndefinedTable: relation "posts" does not exist
```

Shuning uchun sxema modellardan yaratiladi (test to'plami ham xuddi shunday
qiladi), keyin Alembic `head`ga stamp qilinadi — bundan keyingi migratsiyalar
odatdagidek qo'llanaveradi.

---

## 4. Serverni ishga tushirish

```bash
.venv-linux/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

> `8000` porti bu mashinada boshqa konteyner (`sifco_backend`) tomonidan band,
> shuning uchun `8080` ishlatilyapti. Port bo'sh bo'lsa, `--port 8000` ham bo'laveradi.

Tekshirish:

```bash
curl http://127.0.0.1:8080/health          # {"status":"healthy"}
```

Brauzerda:

| Manzil | Nima |
|---|---|
| http://127.0.0.1:8080/docs | **Swagger UI** — imtihonda shuni ko'rsating |
| http://127.0.0.1:8080/redoc | ReDoc |
| http://127.0.0.1:8080/openapi.json | OpenAPI spetsifikatsiyasi (53 endpoint) |

---

## 5. Demo ma'lumot bilan to'ldirish

```bash
.venv-linux/bin/python scripts/seed_demo.py
```

Skript butun biznes-oqimni **haqiqiy HTTP so'rovlar orqali** bosqichma-bosqich
bajaradi va har bir qadamni chop etadi:

1. Platforma admini → `POST /admin/auth/login`
2. Bog'cha ro'yxatdan o'tishi → `POST /auth/register`, `POST /kindergartens/`
3. **RBAC darvozasi**: tasdiqlanmagan bog'cha `403` oladi → admin tasdiqlaydi
4. Tarbiyachi va xodimlar → `POST /teachers/`, `POST /staff/`
5. Guruh → `POST /groups/`
6. 3 ta bola → `POST /children/`
7. Ota-ona hisobi, 2 ta bolaga bog'langan → `POST /kindergartens/parents`
8. Bugungi davomat → `POST /attendance/bulk`, `GET /attendance/daily`
9. Bugungi menyu → `POST /kindergartens/menus`
10. To'lovlar + "to'landi" belgisi → `POST /payments/`, `PATCH /payments/{id}/mark-paid`
11. Guruhga e'lon (fan-out) → `POST /announcements/`
12. **Ota-ona kabineti** o'z tokeni bilan → `/parent/dashboard`, `/parent/menu`,
    `/parent/attendance`, `/parent/payments`, `/parent/notifications`
13. **Tenant izolyatsiyasi**: ikkinchi tasdiqlangan bog'cha bizning guruhni
    o'qiy olmaydi → `404`, va uning ro'yxati bo'sh

### Demo hisoblari

| Rol | Login | Parol |
|---|---|---|
| Platforma admini | `admin@kindlycloud.uz` | `Admin12345!` |
| Bog'cha (direktor) | `director@bogcha.uz` | `Director12345!` |
| Ota-ona | `+998901234567` | `Parent12345!` |

---

## 6. Testlar

```bash
.venv-linux/bin/python -m pytest -q
```

Natija: **129 passed**. Testlar xotiradagi SQLite'da ishlaydi, shuning uchun
ishlayotgan PostgreSQL bazasiga tegmaydi.

---

## 7. Swagger UI'da qo'lda demo qilish

1. http://127.0.0.1:8080/docs ni oching.
2. `POST /api/v1/auth/login` → `{"email": "director@bogcha.uz", "password": "Director12345!"}`
3. Javobdan `access_token` ni nusxalang.
4. Yuqoridagi **Authorize** tugmasini bosib tokenni kiriting.
5. Endi `GET /api/v1/groups/`, `GET /api/v1/children/`,
   `GET /api/v1/attendance/daily`, `GET /api/v1/payments/` ni ishga tushiring.
6. Ota-ona tomonini ko'rsatish uchun `POST /api/v1/auth/parent-login` bilan
   `+998901234567` / `Parent12345!` orqali yangi token oling va qayta Authorize
   qilib `GET /api/v1/parent/dashboard` ni chaqiring.

### Terminaldan (curl) tez demo

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"director@bogcha.uz","password":"Director12345!"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -s http://127.0.0.1:8080/api/v1/groups/ -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 8. To'xtatish / qayta ishga tushirish

```bash
# serverni to'xtatish: uvicorn ishlayotgan terminalda Ctrl+C

# bazani to'xtatish / yoqish
docker stop kindlycloud-db
docker start kindlycloud-db

# bazani butunlay tozalab qaytadan boshlash
.venv-linux/bin/python scripts/init_db.py --drop
.venv-linux/bin/python scripts/seed_demo.py
```
