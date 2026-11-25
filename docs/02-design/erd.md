# Entity Relationship Diagram (ERD)

- **Title**: Database ERD — Learning Management System (LMS)
- **Version**: 1.0
- **Author**: Antigravity Engineering
- **Last Updated**: 2026-11-25

---

## Mermaid ERD

```mermaid
erDiagram
    roles ||--o{ users : "assigned to"
    users ||--o| instructors : "has profile"
    users ||--o| students : "has profile"
    users ||--o{ password_reset_tokens : "requests"

    instructors ||--o{ courses : "primary instructor"
    courses ||--o{ course_instructors : "assigned"
    instructors ||--o{ course_instructors : "teaches"

    courses ||--o{ course_modules : "contains"
    courses ||--o{ batches : "has"
    instructors ||--o{ batches : "leads"

    users ||--o{ enrollments : "enrolls (student)"
    courses ||--o{ enrollments : "enrolled in"
    batches ||--o{ batch_students : "contains"
    users ||--o{ batch_students : "attends (student)"
    enrollments ||--o{ batch_students : "linked to"

    courses ||--o{ lectures : "has"
    course_modules ||--o{ lectures : "organizes"
    courses ||--o{ study_materials : "has"
    course_modules ||--o{ study_materials : "groups"
    lectures ||--o{ study_materials : "attaches"
    users ||--o{ lecture_progress : "completes (student)"
    lectures ||--o{ lecture_progress : "tracked by"

    courses ||--o{ assignments : "defines"
    batches ||--o{ assignments : "targets"
    assignments ||--o{ submissions : "receives"
    users ||--o{ submissions : "submits (student)"
    submissions ||--o| assignment_feedback : "evaluated by"

    courses ||--o{ quizzes : "defines"
    batches ||--o{ quizzes : "targets"
    quizzes ||--o{ questions : "contains"
    questions ||--o{ quiz_options : "has"
    quizzes ||--o{ quiz_attempts : "attempted in"
    users ||--o{ quiz_attempts : "takes (student)"
    quiz_attempts ||--o{ quiz_answers : "records"
    questions ||--o{ quiz_answers : "answered in"
    quiz_options ||--o{ quiz_answers : "selected"

    batches ||--o{ attendance : "tracks"
    users ||--o{ attendance : "marked for (student)"
    attendance ||--o{ attendance_audit_logs : "audits"

    users ||--o{ certificates : "earned by (student)"
    courses ||--o{ certificates : "issued for"
    enrollments ||--o| certificates : "certifies"

    users ||--o{ payments : "paid by (student)"
    courses ||--o{ payments : "fee for"
    enrollments ||--o{ payments : "tracks fee"

    users ||--o{ notifications : "receives"
    courses ||--o{ announcements : "scoped to"
    batches ||--o{ announcements : "scoped to"
```

---

## Core Relationship Summary
- **Users & Profiles**: `roles` (1) -> `users` (N). `users` (1) -> `students` (0..1) and `users` (1) -> `instructors` (0..1). Domain tables reference `users.id` for `student_id` so JWT `current_user.id` matches ownership directly.
- **Courses & Batches**: `courses` (1) -> `course_modules` (N) -> `lectures` (N). `courses` (M) <-> `instructors` (N) via `course_instructors`. `courses` (1) -> `batches` (N).
- **Enrollments & Batch Roster**: `users` (M) <-> `courses` (N) via `enrollments` (unique per `(student_id, course_id)`). `batches` (M) <-> `users` (N) via `batch_students` (unique per `(batch_id, student_id)`), tied to `enrollments`.
- **Assessments**: `assignments` (1) -> `submissions` (N, versioned per student) -> `assignment_feedback` (0..1). `quizzes` (1) -> `questions` (N) -> `quiz_options` (N); `quiz_attempts` (1) -> `quiz_answers` (N).
- **Operations & Finance**: `attendance` (unique per `(batch_id, student_id, session_date)`) -> `attendance_audit_logs` (N). `enrollments` (1) -> `payments` (N) and `enrollments` (1) -> `certificates` (0..1).
