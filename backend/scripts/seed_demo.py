"""Seed a full demo dataset through the real HTTP API.

Usage:
    .venv-linux/bin/python scripts/seed_demo.py [BASE_URL]

Creates: platform admin, a verified kindergarten, teachers, a group, children,
a parent account, attendance, a published menu, payments and an announcement -
then logs in as the parent and prints the aggregated dashboard.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
API = f"{BASE}/api/v1"

ADMIN_EMAIL = "admin@kindlycloud.uz"
ADMIN_PASSWORD = "Admin12345!"
KG_EMAIL = "director@bogcha.uz"
KG_PASSWORD = "Director12345!"
PARENT_PHONE = "+998901234567"
PARENT_PASSWORD = "Parent12345!"

TODAY = date.today()


def step(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def show(label: str, response: httpx.Response) -> dict:
    ok = "OK " if response.is_success else "ERR"
    print(f"[{ok}] {response.status_code} {label}")
    if not response.is_success:
        print("      ->", response.text[:300])
        response.raise_for_status()
    return response.json() if response.content else {}


def ensure_platform_admin() -> None:
    """Platform admins are provisioned out of band, so insert one directly."""
    from app.core.db import SessionLocal
    from app.core.security import get_password_hash
    from app.models.admin import Admin

    db = SessionLocal()
    try:
        if db.query(Admin).filter(Admin.email == ADMIN_EMAIL).first():
            print(f"[OK ] platform admin already exists: {ADMIN_EMAIL}")
            return
        db.add(
            Admin(
                first_name="Platform",
                last_name="Admin",
                phone="+998900000000",
                email=ADMIN_EMAIL,
                password_hash=get_password_hash(ADMIN_PASSWORD),
                role="super_admin",
                status="active",
            )
        )
        db.commit()
        print(f"[OK ] platform admin created: {ADMIN_EMAIL}")
    finally:
        db.close()


def main() -> None:
    client = httpx.Client(timeout=30.0)

    step("0. Health check")
    show("GET /health", client.get(f"{BASE}/health"))

    step("1. Platform admin")
    ensure_platform_admin()
    admin_tokens = show(
        "POST /admin/auth/login",
        client.post(f"{API}/admin/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}),
    )
    admin_h = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

    step("2. Kindergarten registration + profile")
    reg = show(
        "POST /auth/register",
        client.post(
            f"{API}/auth/register",
            json={
                "email": KG_EMAIL,
                "password": KG_PASSWORD,
                "full_name": "Dilnoza Karimova",
                "phone": "+998901112233",
            },
        ),
    )
    kg_h = {"Authorization": f"Bearer {reg['access_token']}"}

    me = show("GET /auth/me", client.get(f"{API}/auth/me", headers=kg_h))
    kg_user_id = me["user_id"]

    kindergarten = show(
        "POST /kindergartens/",
        client.post(
            f"{API}/kindergartens/",
            headers=kg_h,
            json={
                "kinder_name": "Quyoshli Bogcha",
                "region": "Toshkent",
                "district": "Yunusobod",
                "address": "Amir Temur ko'chasi 45",
                "phone": "+998712001020",
                "email": "info@quyoshli.uz",
                "payment_note": "Oylik to'lov har oyning 10-sanasigacha",
            },
        ),
    )
    print(f"      kindergarten_id = {kindergarten['kindergarten_id']}  is_verified = {kindergarten['is_verified']}")

    step("3. Admin verifies the kindergarten (RBAC gate)")
    blocked = client.post(
        f"{API}/groups/",
        headers=kg_h,
        json={
            "name": "Erta guruh",
            "age_from": 3,
            "age_to": 5,
            "capacity": 10,
            "schedule_from": "08:00:00",
            "schedule_to": "18:00:00",
            "monthly_fee": "500000",
        },
    )
    print(f"[OK ] {blocked.status_code} POST /groups/ before verification -> {blocked.json().get('detail')}")

    show(
        f"POST /admin/verify-kindergarten/{kg_user_id}",
        client.post(f"{API}/admin/verify-kindergarten/{kg_user_id}", headers=admin_h),
    )

    step("4. Teachers")
    teacher = show(
        "POST /teachers/",
        client.post(
            f"{API}/teachers/",
            headers=kg_h,
            json={
                "full_name": "Nargiza Xasanova",
                "phone": "+998901999888",
                "role": "teacher",
                "salary": "4500000",
                "hired_at": "2025-09-01",
            },
        ),
    )
    show(
        "POST /staff/ (yordamchi tarbiyachi)",
        client.post(
            f"{API}/staff/",
            headers=kg_h,
            json={
                "full_name": "Gulnora Toshpulatova",
                "phone": "+998901999777",
                "role": "assistant",
                "salary": "3000000",
                "hired_at": "2025-10-01",
            },
        ),
    )

    step("5. Group")
    group = show(
        "POST /groups/",
        client.post(
            f"{API}/groups/",
            headers=kg_h,
            json={
                "name": "Chumolilar guruhi",
                "age_from": 3,
                "age_to": 5,
                "capacity": 20,
                "schedule_from": "08:00:00",
                "schedule_to": "18:00:00",
                "monthly_fee": "850000",
                "teacher_id": teacher["teacher_id"],
            },
        ),
    )
    group_id = group["group_id"]

    step("6. Children")
    children = []
    for full_name, birth, gender in [
        ("Ali Karimov", "2021-05-15", "male"),
        ("Madina Yusupova", "2021-08-02", "female"),
        ("Bekzod Rahimov", "2020-11-20", "male"),
    ]:
        child = show(
            f"POST /children/ ({full_name})",
            client.post(
                f"{API}/children/",
                headers=kg_h,
                json={
                    "full_name": full_name,
                    "birth_date": birth,
                    "gender": gender,
                    "group_id": group_id,
                    "parent_phone": PARENT_PHONE,
                    "notes": "Allergiya yo'q",
                },
            ),
        )
        children.append(child)

    step("7. Parent account linked to two children")
    parent = show(
        "POST /kindergartens/parents",
        client.post(
            f"{API}/kindergartens/parents",
            headers=kg_h,
            json={
                "first_name": "Sardor",
                "last_name": "Karimov",
                "phone": PARENT_PHONE,
                "email": "sardor.karimov@mail.uz",
                "address": "Toshkent, Yunusobod 12-uy",
                "birth_date": "1990-03-25",
                "password": PARENT_PASSWORD,
                "child_ids": [children[0]["child_id"], children[1]["child_id"]],
            },
        ),
    )
    print(f"      parent_id = {parent['parent_id']}")

    step("8. Attendance for today")
    show(
        "POST /attendance/bulk",
        client.post(
            f"{API}/attendance/bulk",
            headers=kg_h,
            json={
                "group_id": group_id,
                "date": TODAY.isoformat(),
                "records": [
                    {"child_id": children[0]["child_id"], "status": "present"},
                    {"child_id": children[1]["child_id"], "status": "late", "note": "20 daqiqa kechikdi"},
                    {"child_id": children[2]["child_id"], "status": "absent", "note": "Kasal"},
                ],
            },
        ),
    )
    daily = show(
        "GET /attendance/daily",
        client.get(f"{API}/attendance/daily", headers=kg_h, params={"group_id": group_id, "date": TODAY.isoformat()}),
    )
    for item in daily["items"]:
        print(f"      - {item['full_name']}: {item['status']}")

    step("9. Today's menu")
    show(
        "POST /kindergartens/menus",
        client.post(
            f"{API}/kindergartens/menus",
            headers=kg_h,
            json={
                "menu_date": TODAY.isoformat(),
                "group_ids": [group_id],
                "notes": "Yong'oqsiz menyu",
                "items": [
                    {"meal": "breakfast", "title": "Sutli bo'tqa", "description": "Guruch bo'tqasi", "calories": 320},
                    {"meal": "lunch", "title": "Mastava", "description": "Go'shtli sho'rva", "calories": 540},
                    {"meal": "snack", "title": "Olma va pechenye", "calories": 180},
                ],
            },
        ),
    )

    step("10. Payments")
    due = TODAY + timedelta(days=20)
    payments = []
    for child in children[:2]:
        payment = show(
            f"POST /payments/ ({child['full_name']})",
            client.post(
                f"{API}/payments/",
                headers=kg_h,
                json={
                    "child_id": child["child_id"],
                    "amount": "850000.00",
                    "due_date": due.isoformat(),
                    "billing_period": due.strftime("%Y-%m"),
                    "notes": "Oylik to'lov",
                },
            ),
        )
        payments.append(payment)

    show(
        "PATCH /payments/{id}/mark-paid",
        client.patch(
            f"{API}/payments/{payments[0]['payment_id']}/mark-paid",
            headers=kg_h,
            json={"payment_method": "cash"},
        ),
    )

    step("11. Announcement fan-out to the group")
    show(
        "POST /announcements/",
        client.post(
            f"{API}/announcements/",
            headers=kg_h,
            json={
                "title": "Ertangi sayr",
                "message": "Ertaga soat 10:00 da bolalar bilan bog'ga sayrga chiqamiz.",
                "target_type": "group",
                "target_group_id": group_id,
            },
        ),
    )

    step("12. Parent portal (parent's own token)")
    parent_tokens = show(
        "POST /auth/parent-login",
        client.post(f"{API}/auth/parent-login", json={"phone_number": PARENT_PHONE, "password": PARENT_PASSWORD}),
    )
    parent_h = {"Authorization": f"Bearer {parent_tokens['access_token']}"}

    dashboard = show("GET /parent/dashboard", client.get(f"{API}/parent/dashboard", headers=parent_h))
    print(f"      o'qilmagan bildirishnomalar: {dashboard['unread_notifications_count']}")
    for entry in dashboard["children"]:
        print(
            f"      - {entry['full_name']}: davomat={entry['today_attendance_status']}, "
            f"guruh={entry['group']['group_name']}, tarbiyachi={(entry.get('pedagogue') or {}).get('full_name')}"
        )
    first_child_id = children[0]["child_id"]
    menu = show(
        "GET /parent/menu",
        client.get(f"{API}/parent/menu", headers=parent_h, params={"child_id": first_child_id}),
    )
    for item in menu.get("items", []):
        print(f"      {item['meal']}: {item['title']}")
    show(
        "GET /parent/attendance",
        client.get(f"{API}/parent/attendance", headers=parent_h, params={"child_id": first_child_id}),
    )
    paid = show("GET /parent/payments", client.get(f"{API}/parent/payments", headers=parent_h))
    for item in paid["items"]:
        print(f"      {item['billing_period']}: {item['amount']} -> {item['status']}")
    notes = show("GET /parent/notifications", client.get(f"{API}/parent/notifications", headers=parent_h))
    for item in notes["items"][:5]:
        print(f"      [{item['type']}] {item['title']}")

    step("13. Tenant isolation: a second verified kindergarten cannot see our data")
    other_reg = show(
        "POST /auth/register (ikkinchi bog'cha)",
        client.post(
            f"{API}/auth/register",
            json={
                "email": "other@bogcha.uz",
                "password": "Other12345!",
                "full_name": "Boshqa Bogcha",
                "phone": "+998905556677",
            },
        ),
    )
    other_h = {"Authorization": f"Bearer {other_reg['access_token']}"}
    other_me = show("GET /auth/me", client.get(f"{API}/auth/me", headers=other_h))
    show(
        "POST /kindergartens/ (ikkinchi bog'cha)",
        client.post(
            f"{API}/kindergartens/",
            headers=other_h,
            json={
                "kinder_name": "Yulduzcha Bogcha",
                "region": "Toshkent",
                "district": "Chilonzor",
                "address": "Bunyodkor 9",
                "phone": "+998712003040",
                "email": "info@yulduzcha.uz",
            },
        ),
    )
    show(
        f"POST /admin/verify-kindergarten/{other_me['user_id']}",
        client.post(f"{API}/admin/verify-kindergarten/{other_me['user_id']}", headers=admin_h),
    )

    leak = client.get(f"{API}/groups/{group_id}", headers=other_h)
    print(f"[OK ] {leak.status_code} GET /groups/{{our group}} as the other tenant -> {leak.json().get('detail')}")
    own = show("GET /groups/ (ikkinchi bog'cha ro'yxati)", client.get(f"{API}/groups/", headers=other_h))
    print(f"      ikkinchi bog'cha guruhlari soni: {own['total']} (bizning guruh ko'rinmaydi)")

    step("DEMO HISOBLARI")
    print(f"  Admin      : {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  Bog'cha    : {KG_EMAIL} / {KG_PASSWORD}")
    print(f"  Ota-ona    : {PARENT_PHONE} / {PARENT_PASSWORD}")
    print(f"  Swagger UI : {BASE}/docs")

    client.close()


if __name__ == "__main__":
    main()
