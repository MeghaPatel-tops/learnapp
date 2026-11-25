# Business Rules and Policy Document

- **Title**: Business Rules and Policy Document
- **Version**: 1.0
- **Author**: Antigravity Engineering
- **Last Updated**: 2026-11-25

---

## 1. Account & Authentication Policy
- **Registration**: Public self-registration is disabled. `POST /api/auth/register` requires an authenticated `admin` user.
- **Password Policy**: Minimum 8 characters, containing at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character. Hashed using Argon2id (`argon2-cffi`).
- **Inactive Accounts**: Users with `is_active = false` cannot log in and existing tokens are rejected when `get_current_user` checks `user.is_active`.
- **Forgot / Reset Password**: Generates a cryptographically random token stored as a SHA-256 hash in `password_reset_tokens` with a 30-minute expiry and single-use `used_at` enforcement.

---

## 2. Course, Batch & Enrollment Rules
- **Course Deletion**: Courses with active enrollments, batches, or financial records cannot be hard-deleted (`409 Conflict`). Admins archive (`status = archived`) or soft-delete (`is_deleted = true`) instead.
- **Batch Date Validation**: `end_date` must be greater than or equal to `start_date`.
- **Batch Capacity**: A student cannot be added to a batch if `active_batch_students >= batch.capacity` (`409 Conflict`) or if the batch status is `closed` or `archived`.
- **Course Enrollment Prerequisite**: A student must have an active `enrollment` in `batch.course_id` before (or atomically during) batch assignment. Duplicate `(student_id, course_id)` enrollments and duplicate `(batch_id, student_id)` memberships are rejected with `409 Conflict`.

---

## 3. Lecture & Study Material Rules
- **Authorization**: Only Admins and Instructors assigned to the course (via `courses.primary_instructor_id`, `course_instructors`, or a batch of that course) can create/update/reorder/delete lectures and materials.
- **Access Control**: Students can view lectures and download study materials **only** for courses in which they have an active/completed enrollment.
- **File Validation**: Allowed types validated by both extension and magic bytes/headers:
  - Videos: `.mp4`, `.webm`, `.mov` (max 500 MB configurable)
  - Study Materials: `.pdf`, `.ppt`, `.pptx`, `.doc`, `.docx`, `.txt`, `.zip` (max 50 MB configurable)
  - Assignment Attachments / Submissions: `.pdf`, `.doc`, `.docx`, `.zip`, `.txt`, `.png`, `.jpg`, `.jpeg` (max 25 MB configurable)
  - Images (Thumbnails/Avatars): `.png`, `.jpg`, `.jpeg`, `.webp` (max 5 MB configurable)

---

## 4. Assignment & Submission Policy
- **Late Submission**: Controlled per assignment via `allow_late` (default `true`).
  - If `submitted_at <= due_date`: status = `submitted`, `is_late = false`.
  - If `submitted_at > due_date` and `allow_late = true`: status = `late_submission`, `is_late = true`.
  - If `submitted_at > due_date` and `allow_late = false`: rejected with `400 Bad Request`.
- **Versioning**: Students may submit new versions while the assignment has not yet been evaluated (`evaluated`), incrementing `version` (`1, 2, ...`). Once evaluated, resubmission is blocked unless an instructor resets/reopens (or new version blocked with `409 Conflict`).
- **Evaluation**: Only Admins or assigned batch/course Instructors may evaluate. `0 <= marks_obtained <= assignment.max_marks`. Evaluating sets submission `status = evaluated` and notifies the student.

---

## 5. Quiz & Examination Policy
- **Availability Window**: Students can start an attempt only if `is_published = true`, `available_from <= now <= available_until`, and the student is enrolled in the target course (and target `batch_id` if specified).
- **Retake Policy**:
  - If `allow_retakes = false`: maximum 1 attempt allowed.
  - If `allow_retakes = true`: up to `max_attempts` allowed (cannot start a new attempt while one is `in_progress`).
- **Timing Enforcement**:
  - `expires_at = min(started_at + duration_minutes, available_until)`.
  - Saving an answer or submitting after `expires_at` finalizes the attempt as `timed_out` and grades all saved answers up to that point.
- **Server-Side Scoring**:
  - `quiz_options.is_correct` is **never** returned in student question/attempt endpoints while `status == in_progress` (and only returned after submission if `quiz.show_correct_answers == true`).
  - On submission/timeout, backend sums `question.marks` for every question whose `selected_option.is_correct == true`. `is_passed = (score >= quiz.passing_marks)`.
- **Best Score Policy**: When calculating student progress and course completion, a student's score for a quiz is `MAX(score)` across all finalized (`submitted` or `timed_out`) attempts.

---

## 6. Attendance Policy & Formula
- **Statuses**: `present`, `absent`, `cancelled`, `holiday`, `approved_leave`.
- **Denominator Rule**: `Cancelled`, `Holiday`, and `Approved Leave` are excluded from eligible classes.
  $$\text{Eligible Classes} = \text{Count}(\text{present}) + \text{Count}(\text{absent})$$
  $$\text{Attendance Percentage} = \begin{cases} \frac{\text{Count}(\text{present})}{\text{Eligible Classes}} \times 100 & \text{if Eligible Classes} > 0 \\ 0.0 & \text{if Eligible Classes} = 0 \end{cases}$$
- **Uniqueness & Audit Trail**: Only one record per `(batch_id, student_id, session_date)`. Updating a record writes an immutable entry in `attendance_audit_logs`.

---

## 7. Course Progress & Completion Policy
- **Progress Metrics** (per student per course):
  - `lecture_completion_pct = (completed_published_lectures / total_published_lectures) * 100` (100% if 0 lectures? No: 0% if 0 lectures exist so empty courses don't auto-complete).
  - `assignments_passed / total_applicable_assignments` (applicable = course-wide assignments + assignments for the student's batch in that course; passed = latest evaluated submission has `marks_obtained >= passing_marks`).
  - `quizzes_passed / total_applicable_quizzes` (applicable = published course-wide or student's batch quizzes; passed = best finalized attempt has `score >= passing_marks`).
  - `overall_progress_pct`: Weighted average of completed items across `(lectures + applicable_assignments + applicable_quizzes)`:
    $$\text{Overall Progress \%} = \frac{\text{Completed Lectures} + \text{Passed Assignments} + \text{Passed Quizzes}}{\text{Total Published Lectures} + \text{Total Applicable Assignments} + \text{Total Applicable Quizzes}} \times 100$$
- **Course Completion Condition** (per Reviewer Agreement):
  1. At least 1 published lecture exists AND **100% of published lectures are marked completed**.
  2. **All applicable assignments** are evaluated and passed (`marks_obtained >= passing_marks`).
  3. **All applicable published quizzes** have at least one finalized attempt with `best_score >= passing_marks`.
  4. (No minimum attendance threshold is required for completion/certificates.)
- When all conditions are met, the enrollment can transition to `completed` (and is auto-checked on lecture completion, assignment evaluation, and quiz submission).

---

## 8. Certificate Policy
- Certificates can only be generated when the student's course completion conditions (Section 7) are satisfied.
- Unique `certificate_number` (e.g., `CERT-YYYY-XXXXXX`) and `verification_code` (UUID/alphanumeric token) are generated once per `(student_id, course_id)`. Duplicate generation is prevented (`409` or returns existing record).
- Public verification endpoint `GET /api/certificates/verify/{code}` returns non-sensitive verification details (student name, course name, issue date, certificate number, valid status).

---

## 9. Payment & Fee Policy
- Total expected fee for an enrollment is derived from `course.fee` (snapshotted on payment records as `total_fee`).
- Supports full and partial payments. Multiple payment transactions can be recorded against an enrollment; net paid = `SUM(amount_paid where status in ('paid', 'partially_paid')) - SUM(amount_paid where status == 'refunded')` (or if a single payment is marked `refunded`, it reduces/reverses that payment).
- New payments cannot exceed remaining pending balance (`pending_amount = total_fee - net_paid`).
- Overall enrollment fee status:
  - `paid` if `net_paid >= total_fee` (and `total_fee > 0` or `0`-fee course)
  - `partially_paid` if `0 < net_paid < total_fee`
  - `pending` if `net_paid == 0`
- Raw card numbers, CVV, or payment gateway secrets are **never** accepted or stored.
