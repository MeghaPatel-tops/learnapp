# Security Architecture Document

- **Title**: Security Document
- **Version**: 1.0
- **Author**: Antigravity Engineering
- **Last Updated**: 2026-11-25

---

## 1. Authentication Approach
- **JWT Bearer Tokens**: Issued at `POST /api/auth/login` using HS256 (or configurable algorithm) signed with `JWT_SECRET_KEY` from environment variables.
- **Claims**: `sub` (string user ID), `role` (`admin` | `instructor` | `student`), `type` (`access`), `iat`, `exp` (configurable `JWT_EXPIRE_MINUTES`, default 60 minutes).
- **Generic Login Errors**: Invalid email, wrong password, and unknown email all return a generic `401 Unauthorized` message (`"Invalid email or password."`) so login cannot be used for email enumeration. Inactive accounts return `403 Forbidden` after credential verification (or generic unauthorized if preferred; here inactive returns `403 Account is deactivated` only after verifying valid credentials, or on token use).
- **Password Hashing**: Argon2id via `argon2-cffi`. Passwords are never stored or logged in plain text and `password_hash` is excluded from all Pydantic response schemas.

---

## 2. Role-Based & Resource-Level Authorization
Every protected route uses FastAPI dependencies:
1. `get_current_user`: Validates Bearer JWT, verifies user exists and `is_active == True`.
2. `require_role(*allowed_roles)`: Enforces coarse-grained RBAC (`admin`, `instructor`, `student`).
3. **Resource-Level Ownership Checks** inside the service layer:
   - **Instructor**: Restricted to courses where `primary_instructor_id == instructor.id` or linked via `course_instructors` or assigned as `batch.instructor_id`, and batches where `batch.instructor_id == current_user.id`.
   - **Student**: Restricted to their own `student_id == current_user.id` records (enrollments, submissions, quiz attempts, attendance, payments, certificates, notifications) and courses/batches they are actively enrolled in.
   - **Admin**: Institute-wide access.

---

## 3. Input Validation, SQL Injection & File Security
- **ORM / Parameterized Queries**: All DB queries use SQLAlchemy 2.0 ORM and bound parameters; no raw string-interpolated SQL.
- **Pydantic Validation**: Strict types, string length bounds, numeric bounds (`ge`, `le`), and email validation (`EmailStr`) on all inputs.
- **Upload Validation**: Extension whitelist + MIME/magic-byte inspection (e.g., `%PDF-` for PDFs, `PK\x03\x04` for Office Open XML / ZIP, PNG/JPEG/WebP signatures, MP4/WebM/MOV signatures) + strict max byte size. Stored filenames use UUIDs, never user-supplied path segments (preventing path traversal).
- **Protected File Serving**: `uploads/` is **not** mounted as an unauthenticated static directory for private course files/submissions/certificates. Downloads go through authorized API endpoints.

---

## 4. Network, Secrets & Operational Security
- **CORS**: Explicit origin whitelist via `CORS_ORIGINS` env variable (no wildcard `*` with credentials).
- **Rate Limiting**: Applied via SlowAPI to `POST /api/auth/login`, `POST /api/auth/forgot-password`, and `POST /api/auth/reset-password`.
- **Secrets Management**: `.env` is gitignored; `.env.example` holds placeholder keys only.
- **Logging Hygiene**: Request logger masks `Authorization`, `password`, `new_password`, `token`, and secret fields.
- **Quiz Anti-Cheat**: Correct answer flags (`is_correct`) are stripped from student payloads until after attempt submission (and only if `show_correct_answers` is enabled). Scores and timers are computed strictly server-side.
