# 🌈KindlyCloud
Kindergarten Management System (SaaS) A role-based web and mobile platform for managing kindergartens, parents, children, attendance, payments, and daily menus. Built with scalable architecture and secure authentication.

# Kindergarten Management System (SaaS)

A scalable, role-based Kindergarten Management Platform designed for managing kindergartens, parents, children, attendance, payments, and notifications.

Built with modern backend architecture using FastAPI and PostgreSQL.

---

## 🚀 Features

### 🔐 Role-Based Authentication
- Admin
- Kindergarten
- Parent

Secure JWT-based authentication system with role-based access control.

---

### 🏫 Kindergarten Panel
-Dashboard
- Manage groups CRUD
- Assign pedagogues  CRUD
- Track attendance CRUD
- Parents 
- Plan daily menus CRUD
- Children
- Receive and respond to feedback CRUD
-Tracking payments
- Create announcements/posts
- Configure business profile & payment info GET/PUT/POST


---

### 👨‍👩‍👧 Parent   Telegram Bot App
- Authentication via phone/email
- View child's group & assigned pedagogue
- View daily menu
- Receive notifications:
  - Attendance updates
  - Payment reminders
  - Pickup reminders
- Make online payments

---

### 👑 Admin Dashboard
- Monitor all kindergartens
- View analytics & system dashboard
- Verify institutions
- Manage feedback
- Remove or confirm kindergartens

---

## 🧱 Tech Stack

- **Backend:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Authentication:** JWT
- **Deployment:** (planned)

---

## 🗂 Database Design

- Users (central authentication system)
- Parents
- Kindergartens
- Pedagogues
- Children
- Groups
- Enrollment
- Attendance
- Payments
- Notifications
- Feedback

---

## 📈 Architecture

Multi-tenant architecture with centralized authentication and role-based access control.

Separate frontends:
- Parent Telegram Bot App
- Kindergarten Web Panel
- Admin Web Dashboard

---
## Updates

Parent during the authentication, enters phone number, receives OTP, enters OTP, enters password, confirms password, and is logged in.

Kindergarten can attach its created pedagogues to groups.

During the creating group, kindergaten can add extra info about group such as age from-to, capacity, room number, monthly fee, active time (8.30-17.30) based on active time parent can get notification when child is late or early.

During the kindergarten authentication, first comes with email or phone number and password, then system checks if the kindergarten is verified, if not, it will send a verification email to the admin, if verified, it will send a verification email to the kindergarten. Then enters its kindergarten info such as name, address[region, city, district, street, payment info.]

Kindergarten is business account, so one business owner can have multiple kindergartens.

Parents can have multiple children, and each child can have multiple parents.


---

## 🎯 Future Improvements

- Payment gateway integration
- Push notifications
- Analytics dashboard
- Subscription-based SaaS model
- Docker deployment
- CI/CD pipeline

---

## 📌 Status

🚧 In Development (MVP Phase)