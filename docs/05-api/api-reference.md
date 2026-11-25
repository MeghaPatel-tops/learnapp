# Learning Management System (LMS) - Complete API Reference

Base URL: `http://127.0.0.1:8000`
Authentication: HTTP Bearer Token (`Authorization: Bearer <JWT_ACCESS_TOKEN>`)

---

## 1. Authentication & Account Management (`/api/auth`)

### 1.1 Login
- **Endpoint**: `POST /api/auth/login`
- **Auth**: None (Public)
- **Rate Limit**: 10 requests / minute
- **Request Body**:
  ```json
  {
    "email": "admin@lms-institute.com",
    "password": "Admin@123456"
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "full_name": "System Administrator",
      "email": "admin@lms-institute.com",
      "phone": null,
      "avatar_url": null,
      "role": "admin",
      "is_active": true,
      "last_login_at": "2026-11-25T09:35:21Z",
      "created_at": "2026-11-25T09:34:25Z",
      "updated_at": "2026-11-25T09:35:21Z"
    }
  }
  ```
- **Errors**: `401 Unauthorized` (`INVALID_CREDENTIALS`), `403 Forbidden` (`ACCOUNT_INACTIVE`), `422 Unprocessable Entity` (`VALIDATION_ERROR`).

---

### 1.2 Admin User Registration
- **Endpoint**: `POST /api/auth/register`
- **Auth**: Admin only
- **Request Body**:
  ```json
  {
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "password": "SecurePassword@123",
    "role": "student", // "admin" | "instructor" | "student"
    "phone": "+1234567890",
    "is_active": true,
    "student_code": "STU-2026-001",
    "date_of_birth": "2000-01-15",
    "address": "123 Academic Way",
    "guardian_name": "Jane Doe",
    "guardian_phone": "+1234567899"
  }
  ```
- **Success Response (201 Created)**: User summary object.
- **Errors**: `400 Bad Request` (`INVALID_ROLE`), `403 Forbidden` (`FORBIDDEN`), `409 Conflict` (`EMAIL_EXISTS`), `422 Unprocessable Entity` (`WEAK_PASSWORD`).

---

### 1.3 Current User Profile
- **Endpoint**: `GET /api/auth/me`
- **Auth**: Required (any active user)
- **Success Response (200 OK)**: User summary.

### 1.4 Update Current User Profile
- **Endpoint**: `PUT /api/auth/me`
- **Auth**: Required (any active user)
- **Request Body**:
  ```json
  {
    "full_name": "Johnathan Doe",
    "phone": "+1987654321",
    "avatar_url": "https://cdn.example.com/avatars/user1.png"
  }
  ```
- **Success Response (200 OK)**: Updated user summary.

---

### 1.5 Change Password
- **Endpoint**: `POST /api/auth/change-password`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "current_password": "OldPassword@123",
    "new_password": "NewPassword@456"
  }
  ```
- **Success Response (200 OK)**: `{"message": "Password changed successfully."}`

---

### 1.6 Password Reset Flow
- **Request Reset**: `POST /api/auth/forgot-password` (Rate limited: 5/min)
  ```json
  { "email": "john.doe@example.com" }
  ```
- **Confirm Reset**: `POST /api/auth/reset-password` (Rate limited: 5/min)
  ```json
  {
    "token": "<RAW_RESET_TOKEN>",
    "new_password": "NewSecurePassword@123"
  }
  ```

---

## 2. User Management (`/api/users`) [Admin Only]

- `GET /api/users`: Paginated search and role/active filtering (`page`, `page_size`, `search`, `role`, `is_active`, `sort_by`, `sort_order`).
- `POST /api/users`: Create user account.
- `GET /api/users/{user_id}`: Fetch single user profile by ID.
- `PUT /api/users/{user_id}`: Update user metadata, role, or active status.
- `DELETE /api/users/{user_id}`: Deactivate user account (prevents self-deactivation).
- `POST /api/users/{user_id}/reset-password`: Administrator-mandated password override.

---

## 3. Student & Instructor Profiles (`/api/students`, `/api/instructors`)

- `GET /api/students`: Paginated list of student profiles (Admin/Instructor).
- `GET /api/students/{student_id}`: Student details, enrollment history, guardian info.
- `PUT /api/students/{student_id}`: Update student specific profile attributes.
- `GET /api/instructors`: Paginated list of instructors.
- `GET /api/instructors/{instructor_id}`: Instructor profile with qualifications and course assignments.
- `PUT /api/instructors/{instructor_id}`: Update instructor qualifications and bio.

---

## 4. Courses & Modules (`/api/courses`)

### 4.1 Course Operations
- `GET /api/courses`: Scoped list (Admin sees all; Instructor sees assigned; Student sees enrolled/published).
- `POST /api/courses`: Create course (Admin).
  ```json
  {
    "course_code": "CS-101",
    "name": "Full-Stack Web Engineering",
    "description": "Comprehensive full stack course with hands-on projects.",
    "category": "Computer Science",
    "duration_hours": 120,
    "fee": "12000.00",
    "status": "draft"
  }
  ```
- `GET /api/courses/{course_id}`: Course details, curriculum modules, assigned instructors.
- `PUT /api/courses/{course_id}`: Update course (Admin or assigned primary instructor).
- `POST /api/courses/{course_id}/publish`: Publish course (Admin only).
- `POST /api/courses/{course_id}/unpublish`: Revert course to draft (Admin only).
- `POST /api/courses/{course_id}/archive`: Archive course (Admin only).
- `DELETE /api/courses/{course_id}`: Delete course if no active enrollments/batches exist.
- `POST /api/courses/{course_id}/instructors`: Assign co-instructor to course.
- `DELETE /api/courses/{course_id}/instructors/{instructor_id}`: Remove co-instructor.

### 4.2 Module Operations
- `GET /api/courses/{course_id}/modules`: List curriculum modules in sequence order.
- `POST /api/courses/{course_id}/modules`: Create curriculum module.
- `PUT /api/courses/{course_id}/modules/{module_id}`: Update module title or sequence.
- `DELETE /api/courses/{course_id}/modules/{module_id}`: Delete module and associated content.

---

## 5. Batches & Enrollments (`/api/batches`, `/api/enrollments`)

### 5.1 Batches
- `GET /api/batches`: List batches filtered by `course_id`, `status`.
- `POST /api/batches`: Create batch with capacity, dates, class days, timing (Admin).
- `GET /api/batches/{batch_id}`: Batch detail with enrolled student roster.
- `PUT /api/batches/{batch_id}`: Update batch schedule or capacity.
- `POST /api/batches/{batch_id}/close`: Close batch to new admissions.
- `POST /api/batches/{batch_id}/archive`: Archive batch.
- `POST /api/batches/{batch_id}/students`: Add enrolled student to batch roster (validates course enrollment & capacity).
- `DELETE /api/batches/{batch_id}/students/{student_id}`: Remove student from batch.

### 5.2 Enrollments
- `GET /api/enrollments`: List course enrollments with student and course metadata.
- `POST /api/enrollments`: Enroll student into a course (Admin only, validates against duplicate enrollments).
- `PUT /api/enrollments/{enrollment_id}`: Update status (`active`, `completed`, `dropped`).

---

## 6. Lectures & Study Materials (`/api/lectures`, `/api/materials`)

### 6.1 Lectures
- `GET /api/lectures`: List lectures for a course/module.
- `POST /api/lectures`: Create lecture (video, document, or live meeting format).
- `GET /api/lectures/{lecture_id}`: View lecture details and stream/download URL.
- `PUT /api/lectures/{lecture_id}`: Update lecture content, sequence, publication state.
- `DELETE /api/lectures/{lecture_id}`: Delete lecture.
- `POST /api/lectures/{lecture_id}/reorder`: Adjust sequence order within module.
- `POST /api/lectures/{lecture_id}/complete`: Student marks lecture as completed.

### 6.2 Study Materials
- `POST /api/materials/upload`: Upload file attachment (validates file magic bytes, extension, size).
- `GET /api/materials`: List study materials by course or lecture.
- `GET /api/materials/{material_id}/download`: Securely download material file stream.
- `DELETE /api/materials/{material_id}`: Delete material.

---

## 7. Assessments: Assignments & Submissions (`/api/assignments`, `/api/submissions`)

### 7.1 Assignments
- `GET /api/assignments`: List assignments for authorized course/batch.
- `POST /api/assignments`: Create assignment with deadline, max marks, passing marks, and `allow_late` policy.
- `GET /api/assignments/{assignment_id}`: View assignment details and instructions.
- `PUT /api/assignments/{assignment_id}`: Update assignment parameters.
- `DELETE /api/assignments/{assignment_id}`: Delete assignment.

### 7.2 Submissions & Evaluation
- `POST /api/assignments/{assignment_id}/submissions`: Student submits solution (supports file upload or text; increments version; validates late policy).
- `GET /api/assignments/{assignment_id}/submissions`: List submissions (Instructor/Admin).
- `GET /api/submissions/{submission_id}`: View submission details and evaluation history.
- `POST /api/submissions/{submission_id}/evaluate`: Instructor grades submission (marks obtained, rubric feedback).

---

## 8. Quizzes & MCQs (`/api/quizzes`)

- `GET /api/quizzes`: List quizzes for course/batch.
- `POST /api/quizzes`: Create quiz (`duration_minutes`, `passing_marks`, `allow_retakes`, `max_attempts`).
- `GET /api/quizzes/{quiz_id}`: Quiz overview.
- `PUT /api/quizzes/{quiz_id}`: Update quiz configurations.
- `POST /api/quizzes/{quiz_id}/publish`: Publish quiz for student access.
- `POST /api/quizzes/{quiz_id}/questions`: Add MCQ questions and options with marks and server-side secret correct option indicators.
- `POST /api/quizzes/{quiz_id}/start`: Student starts attempt (initializes server-side start timestamp and attempt counter).
- `POST /api/quizzes/{quiz_id}/attempts/{attempt_id}/save-answer`: Save answers dynamically during attempt.
- `POST /api/quizzes/{quiz_id}/attempts/{attempt_id}/submit`: Finalize attempt, trigger server-side auto-grading, calculate best score policy.

---

## 9. Attendance Management (`/api/attendance`)

- `POST /api/attendance/bulk`: Mark attendance for an entire batch session (`present`, `absent`, `cancelled`, `holiday`, `approved_leave`).
- `GET /api/attendance`: Filter attendance records by `batch_id`, `student_id`, `session_date`.
- `PUT /api/attendance/{attendance_id}`: Instructor/Admin updates status with mandatory audit log recording (`old_status`, `new_status`, `reason`, `changed_by`).
- `GET /api/attendance/summary`: Compute attendance percentage using verified formula:
  $$\text{Attendance \%} = \frac{\text{Present}}{\text{Present} + \text{Absent}} \times 100$$
  *(Cancelled, Holiday, and Approved Leave are excluded from the denominator)*.

---

## 10. Progress & Course Completion (`/api/progress`)

- `GET /api/progress/courses/{course_id}/students/{student_id}`:
  Evaluates complete academic record against required completion rules:
  1. 100% of published lectures completed.
  2. All applicable assignments submitted, evaluated, and passed ($\ge \text{passing\_marks}$).
  3. All applicable published quizzes passed with best score $\ge \text{passing\_marks}$.
  - When verified, automatically updates enrollment status to `completed` and records `completed_at` timestamp.

---

## 11. Certificates & Public Verification (`/api/certificates`)

- `POST /api/certificates/generate`: Generate official certificate with unique `certificate_number` and `verification_code`. Verifies academic completion before issuance.
- `GET /api/certificates`: List issued certificates.
- `GET /api/certificates/{certificate_id}/download`: Download high-resolution landscape PDF certificate with verification metadata.
- `GET /api/certificates/verify/{verification_code}`: **Public endpoint (No Auth Required)** allowing third parties/employers to verify certificate authenticity.

---

## 12. Fee Payments & Invoicing (`/api/payments`)

- `POST /api/payments`: Record tuition fee payment (cash, card, bank_transfer, upi, online). Validates against overpayment beyond course fee.
- `GET /api/payments`: List payment receipts with pending balance calculation.
- `GET /api/payments/{payment_id}`: Payment receipt details.
- `PUT /api/payments/{payment_id}`: Update payment record or status (e.g. `refunded`).
- `GET /api/payments/{payment_id}/receipt`: Download official PDF fee payment receipt.

---

## 13. Notifications & Announcements (`/api/notifications`, `/api/announcements`)

- `GET /api/notifications`: Get user's notification inbox.
- `PATCH /api/notifications/{notification_id}/read`: Mark notification as read.
- `POST /api/notifications/read-all`: Mark all unread notifications as read.
- `POST /api/announcements`: Publish announcement to institute, course, or specific batch (broadcasts in-app alerts).
- `GET /api/announcements`: Browse announcements scoped to current user's role and enrolled courses.

---

## 14. Dashboards & Reporting (`/api/dashboard`, `/api/reports`)

### 14.1 Dashboard
- `GET /api/dashboard`: Context-aware dynamic dashboard:
  - **Admin**: Institute student/instructor counts, courses, batches, total revenue, pending fees, recent enrollments.
  - **Instructor**: Assigned courses, batches, pending submission evaluations count.
  - **Student**: Enrolled courses, pending assignments, attendance percentage, upcoming schedules.

### 14.2 Reports Export
- `GET /api/reports/{report_type}?format=csv|xlsx|pdf`:
  - Supported `report_type`: `students`, `enrollments`, `payments`, `attendance`, `course-progress`.
  - Formats:
    - `csv`: Raw UTF-8 comma-separated values.
    - `xlsx`: Formatted Microsoft Excel workbook.
    - `pdf`: Branded landscape printable PDF table report.
