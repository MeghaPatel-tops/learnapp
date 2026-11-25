# Requirement Analysis & SRS Notes

- **Title**: Requirement Analysis / SRS Notes — Learning Management System (LMS)
- **Version**: 1.0
- **Author**: Antigravity Engineering
- **Last Updated**: 2026-11-25

---

## 1. Understanding of the Assignment
The project is a full-stack, role-based **Learning Management System (LMS)** for a training institute, built with a **backend-first** approach using **Python FastAPI**, **SQLAlchemy**, **MySQL**, and **JWT authentication** (with React.js + Tailwind CSS frontend to follow after backend completion and approval).

The backend must serve as the single source of truth for:
- Authentication, JWT issuance/validation, and strict role/resource authorization (`admin`, `instructor`, `student`).
- Academic structure: Courses, Course Modules, Batches, Student Enrollments, and Instructor Assignments.
- Learning delivery: Lectures (video URLs and uploaded videos), Study Materials (PDF/PPT/documents), and Lecture Completion tracking.
- Assessments: Assignments (with file attachments, submission versioning, deadline rules, evaluation & feedback) and Timed MCQ Quizzes (with server-side timing, retake controls, and server-side grading).
- Operations: Attendance tracking (with audit trail and leave/holiday/cancelled rules), Student Progress calculation, PDF Certificate generation & public verification, Fee & Payment records with downloadable PDF receipts, In-app Notifications & Announcements, Role-Based Dashboards, and Exportable Reports (CSV/Excel/PDF).

---

## 2. In-Scope vs. Out-of-Scope

### In Scope (Backend Initial Version)
- JWT authentication, password reset workflow, profile management, and Admin-only account creation.
- Role-based access control (Admin, Instructor, Student) enforced on every protected endpoint and file download.
- Full CRUD & lifecycle management for Users, Students, Instructors, Courses, Modules, Batches, Enrollments.
- Lecture & Study Material management with local dev storage (`uploads/`) behind a storage abstraction for production object storage.
- Assignment & Submission workflows (versioning, late submission tagging, instructor evaluation).
- Quiz & MCQ workflows (server-side timer, hidden correct answers before submit, server-side scoring).
- Attendance tracking with audit history and percentage formula.
- Progress calculation, Certificate PDF generation & verification endpoint.
- Fee/Payment tracking, partial payments, and PDF receipt generation.
- In-app Notifications, Announcements, and optional SMTP email dispatch.
- Dashboard analytics and CSV/XLSX/PDF report exports.
- Alembic migrations, synthetic seed data, Swagger/OpenAPI + Postman docs, and Pytest test suite against MySQL.

### Out of Scope (Initial Version)
- AI recommendations, automated tutoring, or AI grading.
- Native mobile apps (Android/iOS).
- Built-in live video conferencing.
- Automated payment gateway settlement / accounting / tax engines.
- Advanced proctoring or biometric attendance.

---

## 3. Clarifications Agreed with Reviewer
1. **Account Creation (`POST /api/auth/register`)**: Admin-only account creation. Public self-registration is disabled; unauthenticated or non-admin requests to create users are rejected with `401`/`403`.
2. **Course Completion & Certificate Eligibility**: A student completes a course and becomes eligible for a certificate when **100% of published lectures are completed** and **all required assignments and quizzes for the course/enrolled batch are passed** (no minimum attendance threshold).
3. **Late Submission & Quiz Retakes**:
   - Assignments have a configurable `allow_late` flag. Late submissions are tagged `late_submission` when allowed, or rejected with `400` when `allow_late=false`.
   - Quizzes have configurable `allow_retakes` and `max_attempts`, and overall quiz performance uses the **best attempt score**.
4. **Attendance Denominator**: `Cancelled`, `Holiday`, and `Approved Leave` records are **excluded from the denominator** (`Total eligible classes = Present + Absent`).
5. **Local Development Database**: Python 3.12 and local MySQL 8.4 Server are used for Alembic migrations and Pytest integration tests.
