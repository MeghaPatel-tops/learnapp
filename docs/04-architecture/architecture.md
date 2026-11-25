# System Architecture Document

- **Title**: System Architecture Document
- **Version**: 1.0
- **Author**: Antigravity Engineering
- **Last Updated**: 2026-11-25

---

## 1. Technology Stack
| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **API Framework** | Python 3.12 + FastAPI | High-performance async/sync REST API, Pydantic v2 validation, OpenAPI/Swagger |
| **ORM & Migrations** | SQLAlchemy 2.0 + Alembic | Relational mapping, parameterized queries, transaction management, versioned schema migrations |
| **Database** | MySQL 8.4 (InnoDB, utf8mb4) | Persistent ACID-compliant relational storage |
| **DB Driver** | PyMySQL + cryptography | Pure-Python MySQL driver with caching_sha2_password support |
| **Authentication** | PyJWT + Argon2id (`argon2-cffi`) | Stateless JWT access tokens + secure salted password hashing |
| **Rate Limiting** | SlowAPI | Request rate limiting on login and password-reset endpoints |
| **PDF & Exports** | ReportLab, OpenPyXL, csv | Certificate PDFs, fee receipt PDFs, tabular CSV/XLSX & printable PDF reports |
| **Testing** | Pytest + FastAPI TestClient | Automated unit and integration testing against MySQL |

---

## 2. High-Level Request & Storage Flow
```text
Client / React Frontend (Future Phase) / Postman
        │  HTTPS / JSON / Multipart Form
        ▼
┌──────────────────────────────────────────────────────────┐
│ FastAPI Application (backend/app/main.py)                │
│  ├─ Middleware: CORS, Request Logging, SlowAPI RateLimit │
│  ├─ Global Exception Handlers (Standard Error Envelope)  │
│  ├─ Dependencies: get_db, get_current_user, require_role │
│  ├─ Routers (/api/...) -> Pydantic Schemas               │
│  └─ Services Layer (Business Logic & Transactions)       │
└───────────────┬──────────────────────────┬───────────────┘
                │ SQLAlchemy ORM           │ Storage Abstraction
                ▼                          ▼
     ┌──────────────────┐       ┌────────────────────────┐
     │ MySQL 8.4 Server │       │ Local uploads/ (Dev)   │
     │  (28 tables)     │       │ Object Storage (Prod)  │
     └──────────────────┘       └────────────────────────┘
```

---

## 3. Backend Folder Structure
```text
backend/
├── app/
│   ├── main.py                # FastAPI app factory, CORS, exception handlers, router registration
│   ├── config.py              # Pydantic Settings loaded from environment (.env)
│   ├── database.py            # SQLAlchemy engine, SessionLocal, DeclarativeBase
│   ├── models/                # SQLAlchemy ORM models (one cohesive module per domain)
│   ├── schemas/               # Pydantic v2 request/response DTOs & standard wrappers
│   ├── routers/               # FastAPI route handlers (thin layer calling services)
│   ├── services/              # Core business logic, authorization checks, DB transactions
│   ├── middleware/            # Request/response logging & rate limiter configuration
│   ├── dependencies/          # Auth (JWT decode, active user check, require_role) & pagination
│   └── utils/                 # Password hashing, JWT helpers, file storage, PDF/CSV/XLSX generators
├── migrations/                # Alembic migration environment and version scripts
├── tests/                     # Pytest suite (conftest + per-module test files)
├── uploads/                   # Development file storage (never committed to Git)
├── alembic.ini
├── requirements.txt
├── seed.py                    # Synthetic initial dataset seeder
└── .env.example               # Placeholder environment variables
```

---

## 4. API & Error-Handling Architecture
- **URL Prefix**: All domain APIs live under `/api/<resource>` (plus `/api/health` for deployment readiness).
- **Pagination & Filtering**: List endpoints accept `page` (default `1`), `page_size` (default `20`, max `100`), `search`, `sort_by`, `sort_order` (`asc`/`desc`), and resource-specific filters, returning a consistent paginated envelope:
  ```json
  {
    "items": [...],
    "total": 42,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
  ```
- **Standard Error Envelope**:
  ```json
  {
    "error": {
      "code": "FORBIDDEN",
      "message": "You do not have permission to access this resource.",
      "details": null
    }
  }
  ```
- **Transactions**: Multi-step operations (student enrollment + batch assignment, assignment evaluation + notification + completion check, attendance update + audit log, quiz submission + answer grading + completion check) execute inside a single SQLAlchemy transaction (`commit` on success, `rollback` on failure).

---

## 5. File & Media Storage Architecture
- Binary files (lecture videos, PDF/PPT study materials, assignment attachments, student submissions, generated certificate PDFs) are **never** stored as BLOBs in MySQL.
- `utils/file_storage.py` defines a storage interface (`LocalStorageBackend` for development under `backend/uploads/`, swappable with S3-compatible object storage in production via env config).
- Private files are served **only** through authenticated FastAPI download endpoints (e.g. `GET /api/materials/{id}/download`, `GET /api/submissions/{id}/download`, `GET /api/certificates/{id}/download`) that verify role and course/batch/ownership permissions before streaming the file.
- Uploaded files are sanitized (UUID storage keys), size-checked, extension-checked, and magic-byte verified.

---

## 6. Third-Party & External Integrations
- **Email Service (Optional SMTP)**: Configurable via `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`. Used for password reset links and optional notification emails; safely logs/skips when disabled in local/test mode.
- **Object Storage (Production)**: S3-compatible bucket settings (`STORAGE_BACKEND=local|s3`, `S3_BUCKET`, `S3_ENDPOINT`, etc.) for persistent production uploads.
