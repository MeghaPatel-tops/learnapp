# Use Cases and User Stories

- **Title**: Use Cases and User Stories
- **Version**: 1.0
- **Author**: Antigravity Engineering
- **Last Updated**: 2026-11-25

---

## 1. Actors
| Actor | Description |
| :--- | :--- |
| **Admin** | Institute administrator with full access to users, courses, batches, payments, certificates, announcements, and institute-wide reports. |
| **Instructor** | Faculty member assigned to specific courses/batches; manages lectures, materials, assignments, quizzes, attendance, evaluations, and batch reports. |
| **Student** | Enrolled learner; views enrolled courses, lectures, materials; submits assignments, attempts quizzes, views own attendance, progress, payments, and downloads certificates. |
| **Public / Unauthenticated** | Can only access health check, login, forgot/reset password, and public certificate verification by unique code. |

---

## 2. User Stories & Acceptance Criteria

### Admin
- **US-A1 (User Management)**: As an Admin, I can create, list, filter, update, reset passwords for, and deactivate user accounts so that only authorized personnel and students access the LMS.
  - *AC*: Unique email enforced; password hashed with Argon2; inactive users cannot log in; non-admins receive `403`.
- **US-A2 (Course & Module Management)**: As an Admin, I can create, publish, unpublish, archive, and organize courses into modules, and assign instructors.
  - *AC*: Courses with active enrollments cannot be hard-deleted (`409 Conflict`); archived/unpublished courses restrict new enrollments.
- **US-A3 (Batch & Enrollment Management)**: As an Admin, I can create batches with date ranges and capacities, enroll students into courses, and assign students to batches.
  - *AC*: Cannot enroll beyond batch capacity (`409`); `end_date >= start_date`; duplicate student-course enrollment or student-batch assignment prevented (`409`).
- **US-A4 (Payment & Fee Management)**: As an Admin, I can record full or partial fee payments, update payment status (including refunds), and generate receipts.
  - *AC*: Overpayment above course fee is rejected; receipt numbers are unique; payment history and pending balances remain consistent.
- **US-A5 (Institute Reports & Announcements)**: As an Admin, I can publish announcements to specific roles, courses, or batches and export CSV/Excel/PDF reports.

### Instructor
- **US-I1 (Content Publishing)**: As an Instructor, I can create/reorder lectures (video URL or uploaded video) and upload study materials (PDF/PPT) for courses I am assigned to.
  - *AC*: Attempting to modify an unassigned course returns `403`; file type and size are validated server-side.
- **US-I2 (Assignments & Evaluation)**: As an Instructor, I can create assignments for my assigned courses/batches, review submissions, and assign marks and feedback.
  - *AC*: Marks cannot exceed `max_marks` (`422`/`400`); student receives notification upon evaluation.
- **US-I3 (Quizzes)**: As an Instructor, I can create timed MCQ quizzes with questions/options for assigned batches and view student results.
  - *AC*: Total marks validated; correct answers never returned to students prior to submission.
- **US-I4 (Attendance)**: As an Instructor, I can mark daily attendance for students in my assigned batches and update records with an audit reason.
  - *AC*: Duplicate attendance for `(batch_id, student_id, session_date)` prevented; updates write to `attendance_audit_logs`.

### Student
- **US-S1 (Learning & Progress)**: As a Student, I can access lectures and download study materials only for courses I am enrolled in, and mark lectures completed.
  - *AC*: Accessing another course's private files returns `403`.
- **US-S2 (Assignments)**: As a Student, I can view assigned work, upload submissions, and view my marks and feedback.
  - *AC*: Cannot view other students' submissions (`403`); late submissions blocked or tagged per assignment `allow_late`.
- **US-S3 (Timed Quizzes)**: As a Student, I can start a quiz within its availability window, save answers, and submit for server-side grading.
  - *AC*: Expired attempts auto-finalize as `timed_out`; retake limits enforced; score computed strictly on backend.
- **US-S4 (Certificates & Payments)**: As a Student, I can view my payment history/receipts and download my PDF certificate once course completion rules are met.
  - *AC*: Incomplete courses cannot generate certificates (`400`/`403`); certificate verification endpoint validates authenticity publicly.
