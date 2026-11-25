# Master Project Prompt

- **Title**: Master Project Prompt — Learning Management System (LMS)
- **Version**: 1.0
- **Author**: Antigravity Engineering
- **Last Updated**: 2026-11-25

---

```text
ROLE       : You are a senior full-stack engineer helping build an LMS.
PROJECT    : Role-based Learning Management System (Admin, Instructor, Student).
TECH STACK : React.js + Tailwind CSS | FastAPI | SQLAlchemy | MySQL | JWT.
STRUCTURE  : Follow the frontend/ and backend/ folder structure given.
RULES      : Backend enforces all permissions; no hardcoded data; validate all
             input; hash passwords; no secrets in code; use Alembic migrations.
             Admin-only account registration; 100% lectures + all assignments/quizzes
             passed for course completion; per-assignment allow_late & per-quiz
             allow_retakes/max_attempts (best score); exclude Cancelled/Holiday/
             Approved Leave from attendance denominator.
WORKFLOW   : Backend-first development. Build ONE module at a time:
             models -> schemas -> services -> routers -> tests -> docs.
             Do not start frontend until backend is verified and approved.
OUTPUT     : Explain files created, list assumptions, and verify with Pytest on MySQL.
```
