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
- Pedagogue (Teacher)

Secure JWT-based authentication system with role-based access control.

---

### 🏫 Kindergarten Panel
- Manage groups
- Assign pedagogues
- Track attendance
- Plan daily menus
- Manage children enrollments
- Receive and respond to feedback
- Configure business profile & payment info

---

### 👨‍👩‍👧 Parent App
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
- Parent Mobile App
- Kindergarten Web Panel
- Admin Web Dashboard

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