# Database Data Dictionary

- **Title**: Database Data Dictionary
- **Version**: 1.0
- **Author**: Antigravity Engineering
- **Last Updated**: 2026-11-25
- **Database Engine**: MySQL 8.4 (InnoDB, `utf8mb4_unicode_ci`)

---

## Delete Behaviour Legend
- **RESTRICT**: Prevents parent deletion if child records exist (protects enrollments, financial records, certificates, active courses).
- **CASCADE**: Child rows are automatically deleted when the parent is deleted (e.g., questions when quiz is deleted, options when question is deleted, audit logs with attendance).
- **SET NULL**: Preserves historical records when an optional reference (e.g., `created_by`, `evaluator_id`, `module_id`) is removed.
- **SOFT DELETE / ARCHIVE**: `courses.is_deleted` / `status = archived`, `users.is_active = false`, `batches.status = archived`.

---

## Tables (28 Tables)

### 1. `roles`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Role primary key |
| `name` | `VARCHAR(30)` | UNIQUE, NOT NULL | `admin`, `instructor`, `student` |
| `description` | `VARCHAR(255)` | NULL | Role summary |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL, ON UPDATE CURRENT_TIMESTAMP | Last update timestamp |

### 2. `users`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | User primary key |
| `role_id` | `INT` | FK -> `roles.id` (RESTRICT), INDEX, NOT NULL | Assigned role |
| `full_name` | `VARCHAR(120)` | NOT NULL, INDEX | Full display name |
| `email` | `VARCHAR(255)` | UNIQUE, INDEX, NOT NULL | Login email |
| `password_hash` | `VARCHAR(255)` | NOT NULL | Argon2id password hash |
| `phone` | `VARCHAR(30)` | NULL | Contact phone |
| `avatar_url` | `VARCHAR(500)` | NULL | Profile avatar path/URL |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT TRUE, INDEX | Account active status |
| `last_login_at` | `DATETIME` | NULL | Last successful login |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 3. `password_reset_tokens`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Token record ID |
| `user_id` | `INT` | FK -> `users.id` (CASCADE), INDEX, NOT NULL | Target user |
| `token_hash` | `VARCHAR(64)` | UNIQUE, NOT NULL | SHA-256 hash of reset token |
| `expires_at` | `DATETIME` | NOT NULL | Expiration timestamp |
| `used_at` | `DATETIME` | NULL | Timestamp when consumed |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |

### 4. `instructors`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Instructor profile ID |
| `user_id` | `INT` | UNIQUE, FK -> `users.id` (CASCADE), NOT NULL | Linked user account |
| `employee_code` | `VARCHAR(50)` | UNIQUE, NOT NULL | Institute employee code |
| `expertise` | `VARCHAR(255)` | NULL | Subject expertise areas |
| `qualification` | `VARCHAR(255)` | NULL | Academic qualification |
| `bio` | `TEXT` | NULL | Short instructor biography |
| `experience_years` | `INT` | NOT NULL, DEFAULT 0 | Years of teaching experience |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 5. `students`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Student profile ID |
| `user_id` | `INT` | UNIQUE, FK -> `users.id` (CASCADE), NOT NULL | Linked user account |
| `student_code` | `VARCHAR(50)` | UNIQUE, NOT NULL | Institute student roll/ID |
| `date_of_birth` | `DATE` | NULL | Date of birth |
| `address` | `VARCHAR(500)` | NULL | Residential address |
| `guardian_name` | `VARCHAR(120)` | NULL | Guardian contact name |
| `guardian_phone` | `VARCHAR(30)` | NULL | Guardian contact phone |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 6. `courses`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Course primary key |
| `course_code` | `VARCHAR(50)` | UNIQUE, NOT NULL | Unique course code (e.g. PY-101) |
| `name` | `VARCHAR(200)` | NOT NULL, INDEX | Course title |
| `description` | `TEXT` | NOT NULL | Detailed course overview |
| `category` | `VARCHAR(100)` | NOT NULL, INDEX | Course category |
| `duration_hours` | `INT` | NOT NULL | Total duration in hours |
| `fee` | `DECIMAL(10,2)` | NOT NULL, DEFAULT 0.00 | Standard course fee |
| `thumbnail_url` | `VARCHAR(500)` | NULL | Thumbnail image URL/key |
| `status` | `ENUM('draft','published','archived')` | NOT NULL, DEFAULT 'draft', INDEX | Publication status |
| `primary_instructor_id` | `INT` | FK -> `instructors.id` (SET NULL), NULL | Lead instructor profile |
| `is_deleted` | `BOOLEAN` | NOT NULL, DEFAULT FALSE, INDEX | Soft-delete flag |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 7. `course_instructors`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Mapping ID |
| `course_id` | `INT` | FK -> `courses.id` (CASCADE), NOT NULL | Assigned course |
| `instructor_id` | `INT` | FK -> `instructors.id` (CASCADE), NOT NULL | Assigned instructor |
| `assigned_at` | `DATETIME` | NOT NULL | Assignment timestamp |
| *Constraint* | `UNIQUE(course_id, instructor_id)` | | Prevent duplicate assignment |

### 8. `course_modules`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Module ID |
| `course_id` | `INT` | FK -> `courses.id` (CASCADE), INDEX, NOT NULL | Parent course |
| `title` | `VARCHAR(200)` | NOT NULL | Module title |
| `description` | `TEXT` | NULL | Module summary |
| `sequence_order` | `INT` | NOT NULL, DEFAULT 1 | Display order within course |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 9. `batches`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Batch ID |
| `batch_code` | `VARCHAR(50)` | UNIQUE, NOT NULL | Unique batch code |
| `name` | `VARCHAR(150)` | NOT NULL, INDEX | Batch name |
| `course_id` | `INT` | FK -> `courses.id` (RESTRICT), INDEX, NOT NULL | Linked course |
| `instructor_id` | `INT` | FK -> `instructors.id` (RESTRICT), INDEX, NOT NULL | Assigned batch instructor |
| `start_date` | `DATE` | NOT NULL | Batch start date |
| `end_date` | `DATE` | NOT NULL | Batch end date |
| `class_days` | `VARCHAR(100)` | NOT NULL | e.g. `Mon,Wed,Fri` |
| `class_timing` | `VARCHAR(100)` | NOT NULL | e.g. `10:00 AM - 12:00 PM` |
| `capacity` | `INT` | NOT NULL | Maximum student seats |
| `status` | `ENUM('upcoming','active','closed','archived')` | NOT NULL, DEFAULT 'upcoming', INDEX | Batch lifecycle state |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 10. `enrollments`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Enrollment ID |
| `student_id` | `INT` | FK -> `users.id` (RESTRICT), INDEX, NOT NULL | Enrolled student (`users.id`) |
| `course_id` | `INT` | FK -> `courses.id` (RESTRICT), INDEX, NOT NULL | Enrolled course |
| `status` | `ENUM('active','completed','dropped')` | NOT NULL, DEFAULT 'active', INDEX | Enrollment state |
| `enrolled_at` | `DATETIME` | NOT NULL | Enrollment timestamp |
| `completed_at` | `DATETIME` | NULL | Course completion timestamp |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |
| *Constraint* | `UNIQUE(student_id, course_id)` | | Prevent duplicate enrollment |

### 11. `batch_students`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Roster ID |
| `batch_id` | `INT` | FK -> `batches.id` (CASCADE), INDEX, NOT NULL | Target batch |
| `student_id` | `INT` | FK -> `users.id` (CASCADE), INDEX, NOT NULL | Student (`users.id`) |
| `enrollment_id` | `INT` | FK -> `enrollments.id` (RESTRICT), NOT NULL | Linked course enrollment |
| `status` | `ENUM('active','removed','completed')` | NOT NULL, DEFAULT 'active' | Membership status |
| `joined_at` | `DATETIME` | NOT NULL | Date added to batch |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |
| *Constraint* | `UNIQUE(batch_id, student_id)` | | Prevent duplicate batch roster entry |

### 12. `lectures`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Lecture ID |
| `course_id` | `INT` | FK -> `courses.id` (CASCADE), INDEX, NOT NULL | Parent course |
| `module_id` | `INT` | FK -> `course_modules.id` (CASCADE), INDEX, NOT NULL | Parent module |
| `title` | `VARCHAR(200)` | NOT NULL | Lecture title |
| `description` | `TEXT` | NULL | Lecture summary |
| `sequence_order` | `INT` | NOT NULL, DEFAULT 1 | Order inside module |
| `video_url` | `VARCHAR(500)` | NULL | External video link |
| `video_storage_key` | `VARCHAR(500)` | NULL | Uploaded video storage key |
| `video_file_name` | `VARCHAR(255)` | NULL | Original uploaded video filename |
| `video_mime_type` | `VARCHAR(100)` | NULL | Video MIME type |
| `video_file_size` | `BIGINT` | NULL | Size in bytes |
| `duration_minutes` | `INT` | NOT NULL, DEFAULT 0 | Duration in minutes |
| `is_published` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | Visibility to students |
| `created_by` | `INT` | FK -> `users.id` (SET NULL), NULL | Author user |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 13. `study_materials`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Material ID |
| `course_id` | `INT` | FK -> `courses.id` (CASCADE), INDEX, NOT NULL | Parent course |
| `module_id` | `INT` | FK -> `course_modules.id` (SET NULL), NULL | Optional module |
| `lecture_id` | `INT` | FK -> `lectures.id` (SET NULL), NULL | Optional lecture |
| `title` | `VARCHAR(200)` | NOT NULL | Material title |
| `description` | `TEXT` | NULL | Material notes |
| `file_name` | `VARCHAR(255)` | NOT NULL | Original filename |
| `storage_key` | `VARCHAR(500)` | NOT NULL | Storage object/path key |
| `mime_type` | `VARCHAR(100)` | NOT NULL | Verified MIME type |
| `file_size` | `BIGINT` | NOT NULL | File size in bytes |
| `uploaded_by` | `INT` | FK -> `users.id` (SET NULL), NULL | Uploader user |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 14. `lecture_progress`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Progress record ID |
| `student_id` | `INT` | FK -> `users.id` (CASCADE), INDEX, NOT NULL | Student (`users.id`) |
| `lecture_id` | `INT` | FK -> `lectures.id` (CASCADE), INDEX, NOT NULL | Lecture ID |
| `is_completed` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | Completion flag |
| `completed_at` | `DATETIME` | NULL | Timestamp marked complete |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |
| *Constraint* | `UNIQUE(student_id, lecture_id)` | | Prevent duplicate progress rows |

### 15. `assignments`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Assignment ID |
| `course_id` | `INT` | FK -> `courses.id` (CASCADE), INDEX, NOT NULL | Course ID |
| `batch_id` | `INT` | FK -> `batches.id` (CASCADE), INDEX, NULL | Optional target batch |
| `title` | `VARCHAR(200)` | NOT NULL | Assignment title |
| `instructions` | `TEXT` | NOT NULL | Task instructions |
| `attachment_name` | `VARCHAR(255)` | NULL | Reference file name |
| `attachment_key` | `VARCHAR(500)` | NULL | Reference file storage key |
| `attachment_mime` | `VARCHAR(100)` | NULL | Reference file MIME |
| `attachment_size` | `BIGINT` | NULL | Reference file size |
| `max_marks` | `DECIMAL(6,2)` | NOT NULL | Maximum achievable marks |
| `passing_marks` | `DECIMAL(6,2)` | NOT NULL, DEFAULT 0.00 | Minimum marks to pass |
| `due_date` | `DATETIME` | NOT NULL, INDEX | Submission deadline (UTC) |
| `allow_late` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | Whether late submissions are permitted |
| `created_by` | `INT` | FK -> `users.id` (SET NULL), NULL | Creator user |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 16. `submissions`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Submission ID |
| `assignment_id` | `INT` | FK -> `assignments.id` (CASCADE), INDEX, NOT NULL | Target assignment |
| `student_id` | `INT` | FK -> `users.id` (CASCADE), INDEX, NOT NULL | Student (`users.id`) |
| `version` | `INT` | NOT NULL, DEFAULT 1 | Submission version number |
| `submission_text` | `TEXT` | NULL | Text answer |
| `file_name` | `VARCHAR(255)` | NULL | Uploaded file name |
| `storage_key` | `VARCHAR(500)` | NULL | Uploaded file storage key |
| `mime_type` | `VARCHAR(100)` | NULL | Verified MIME type |
| `file_size` | `BIGINT` | NULL | File size in bytes |
| `status` | `ENUM('pending','submitted','under_review','evaluated','late_submission')` | NOT NULL, DEFAULT 'submitted', INDEX | Workflow status |
| `is_late` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | Submitted after due_date |
| `submitted_at` | `DATETIME` | NOT NULL | Server-recorded submit timestamp |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |
| *Constraint* | `UNIQUE(assignment_id, student_id, version)` | | Versioned submission history |

### 17. `assignment_feedback`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Feedback ID |
| `submission_id` | `INT` | UNIQUE, FK -> `submissions.id` (CASCADE), NOT NULL | Evaluated submission |
| `evaluator_id` | `INT` | FK -> `users.id` (SET NULL), NULL | Grading instructor/admin |
| `marks_obtained` | `DECIMAL(6,2)` | NOT NULL | Awarded marks |
| `feedback_text` | `TEXT` | NULL | Written instructor remarks |
| `evaluated_at` | `DATETIME` | NOT NULL | Evaluation timestamp |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 18. `quizzes`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Quiz ID |
| `course_id` | `INT` | FK -> `courses.id` (CASCADE), INDEX, NOT NULL | Linked course |
| `batch_id` | `INT` | FK -> `batches.id` (CASCADE), INDEX, NULL | Optional target batch |
| `title` | `VARCHAR(200)` | NOT NULL | Quiz title |
| `description` | `TEXT` | NULL | Quiz instructions |
| `total_marks` | `DECIMAL(6,2)` | NOT NULL | Configured total marks |
| `passing_marks` | `DECIMAL(6,2)` | NOT NULL | Minimum passing marks |
| `duration_minutes` | `INT` | NOT NULL | Time limit in minutes |
| `available_from` | `DATETIME` | NOT NULL | Window start (UTC) |
| `available_until` | `DATETIME` | NOT NULL | Window end (UTC) |
| `allow_retakes` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | Allow multiple attempts |
| `max_attempts` | `INT` | NOT NULL, DEFAULT 1 | Max attempts per student |
| `show_correct_answers` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | Allow post-submit answer review |
| `is_published` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | Availability flag |
| `created_by` | `INT` | FK -> `users.id` (SET NULL), NULL | Author user |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 19. `questions`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Question ID |
| `quiz_id` | `INT` | FK -> `quizzes.id` (CASCADE), INDEX, NOT NULL | Parent quiz |
| `question_text` | `TEXT` | NOT NULL | Question prompt |
| `marks` | `DECIMAL(6,2)` | NOT NULL, DEFAULT 1.00 | Question mark weight |
| `sequence_order` | `INT` | NOT NULL, DEFAULT 1 | Question order |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 20. `quiz_options`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Option ID |
| `question_id` | `INT` | FK -> `questions.id` (CASCADE), INDEX, NOT NULL | Parent question |
| `option_text` | `VARCHAR(500)` | NOT NULL | Choice label |
| `is_correct` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | Correct choice indicator |
| `sequence_order` | `INT` | NOT NULL, DEFAULT 1 | Display order |

### 21. `quiz_attempts`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Attempt ID |
| `quiz_id` | `INT` | FK -> `quizzes.id` (CASCADE), INDEX, NOT NULL | Quiz ID |
| `student_id` | `INT` | FK -> `users.id` (CASCADE), INDEX, NOT NULL | Student (`users.id`) |
| `attempt_number` | `INT` | NOT NULL, DEFAULT 1 | Sequential attempt count |
| `started_at` | `DATETIME` | NOT NULL | Backend start timestamp |
| `expires_at` | `DATETIME` | NOT NULL | Backend hard deadline |
| `submitted_at` | `DATETIME` | NULL | Actual submission timestamp |
| `status` | `ENUM('in_progress','submitted','timed_out')` | NOT NULL, DEFAULT 'in_progress' | Attempt state |
| `score` | `DECIMAL(6,2)` | NOT NULL, DEFAULT 0.00 | Server-calculated score |
| `is_passed` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | Whether score >= passing_marks |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |
| *Constraint* | `UNIQUE(quiz_id, student_id, attempt_number)` | | Enforce unique attempt sequence |

### 22. `quiz_answers`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Answer ID |
| `attempt_id` | `INT` | FK -> `quiz_attempts.id` (CASCADE), INDEX, NOT NULL | Attempt ID |
| `question_id` | `INT` | FK -> `questions.id` (CASCADE), NOT NULL | Question ID |
| `selected_option_id` | `INT` | FK -> `quiz_options.id` (SET NULL), NULL | Selected MCQ option |
| `is_correct` | `BOOLEAN` | NULL | Evaluated correctness |
| `marks_awarded` | `DECIMAL(6,2)` | NOT NULL, DEFAULT 0.00 | Marks awarded |
| `answered_at` | `DATETIME` | NOT NULL | Timestamp saved |
| *Constraint* | `UNIQUE(attempt_id, question_id)` | | One answer per question per attempt |

### 23. `attendance`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Attendance ID |
| `batch_id` | `INT` | FK -> `batches.id` (CASCADE), INDEX, NOT NULL | Batch ID |
| `student_id` | `INT` | FK -> `users.id` (CASCADE), INDEX, NOT NULL | Student (`users.id`) |
| `session_date` | `DATE` | NOT NULL, INDEX | Class session date |
| `status` | `ENUM('present','absent','cancelled','holiday','approved_leave')` | NOT NULL | Attendance state |
| `remarks` | `VARCHAR(255)` | NULL | Optional remarks |
| `marked_by` | `INT` | FK -> `users.id` (SET NULL), NULL | Original marker |
| `updated_by` | `INT` | FK -> `users.id` (SET NULL), NULL | Last editor |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |
| *Constraint* | `UNIQUE(batch_id, student_id, session_date)` | | Prevent duplicate attendance per session |

### 24. `attendance_audit_logs`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Audit log ID |
| `attendance_id` | `INT` | FK -> `attendance.id` (CASCADE), INDEX, NOT NULL | Attendance record |
| `old_status` | `VARCHAR(30)` | NOT NULL | Previous status |
| `new_status` | `VARCHAR(30)` | NOT NULL | Updated status |
| `changed_by` | `INT` | FK -> `users.id` (SET NULL), NULL | Editor user ID |
| `reason` | `VARCHAR(255)` | NULL | Reason for change |
| `changed_at` | `DATETIME` | NOT NULL | Audit timestamp |

### 25. `certificates`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Certificate ID |
| `certificate_number` | `VARCHAR(64)` | UNIQUE, INDEX, NOT NULL | Human-readable serial number |
| `verification_code` | `VARCHAR(64)` | UNIQUE, INDEX, NOT NULL | Public verification token |
| `student_id` | `INT` | FK -> `users.id` (RESTRICT), INDEX, NOT NULL | Recipient student |
| `course_id` | `INT` | FK -> `courses.id` (RESTRICT), INDEX, NOT NULL | Completed course |
| `enrollment_id` | `INT` | UNIQUE, FK -> `enrollments.id` (RESTRICT), NOT NULL | Certified enrollment |
| `issued_at` | `DATETIME` | NOT NULL | Issue timestamp |
| `pdf_storage_key` | `VARCHAR(500)` | NULL | Stored PDF certificate key |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| *Constraint* | `UNIQUE(student_id, course_id)` | | Prevent duplicate certificates |

### 26. `payments`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Payment record ID |
| `receipt_number` | `VARCHAR(64)` | UNIQUE, INDEX, NOT NULL | Unique receipt identifier |
| `student_id` | `INT` | FK -> `users.id` (RESTRICT), INDEX, NOT NULL | Student (`users.id`) |
| `course_id` | `INT` | FK -> `courses.id` (RESTRICT), INDEX, NOT NULL | Course ID |
| `enrollment_id` | `INT` | FK -> `enrollments.id` (RESTRICT), INDEX, NOT NULL | Enrollment ID |
| `total_fee` | `DECIMAL(10,2)` | NOT NULL | Applicable course fee |
| `amount_paid` | `DECIMAL(10,2)` | NOT NULL | Amount in this transaction |
| `payment_method` | `ENUM('cash','card','bank_transfer','upi','online','other')` | NOT NULL | Payment method (no raw card data) |
| `transaction_ref` | `VARCHAR(120)` | NULL | External/manual reference ID |
| `status` | `ENUM('paid','partially_paid','pending','failed','refunded')` | NOT NULL, INDEX | Payment status |
| `payment_date` | `DATETIME` | NOT NULL, INDEX | Payment timestamp |
| `notes` | `VARCHAR(500)` | NULL | Admin remarks |
| `recorded_by` | `INT` | FK -> `users.id` (SET NULL), NULL | Admin who recorded payment |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |

### 27. `notifications`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Notification ID |
| `user_id` | `INT` | FK -> `users.id` (CASCADE), INDEX, NOT NULL | Recipient user |
| `title` | `VARCHAR(200)` | NOT NULL | Notification headline |
| `message` | `TEXT` | NOT NULL | Notification body |
| `event_type` | `VARCHAR(60)` | NOT NULL, INDEX | Event category |
| `reference_type` | `VARCHAR(60)` | NULL | Linked entity type |
| `reference_id` | `INT` | NULL | Linked entity ID |
| `is_read` | `BOOLEAN` | NOT NULL, DEFAULT FALSE, INDEX | Read status |
| `read_at` | `DATETIME` | NULL | Timestamp marked read |
| `created_at` | `DATETIME` | NOT NULL, INDEX | Creation timestamp |

### 28. `announcements`
| Column | Type | Keys / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | PK, AUTO_INCREMENT | Announcement ID |
| `title` | `VARCHAR(200)` | NOT NULL | Announcement title |
| `content` | `TEXT` | NOT NULL | Announcement body |
| `target_role` | `ENUM('all','admin','instructor','student')` | NULL, INDEX | Target role scope |
| `course_id` | `INT` | FK -> `courses.id` (CASCADE), INDEX, NULL | Optional course filter |
| `batch_id` | `INT` | FK -> `batches.id` (CASCADE), INDEX, NULL | Optional batch filter |
| `created_by` | `INT` | FK -> `users.id` (SET NULL), NULL | Publisher user |
| `published_at` | `DATETIME` | NOT NULL, INDEX | Publication timestamp |
| `created_at` | `DATETIME` | NOT NULL | Creation timestamp |
| `updated_at` | `DATETIME` | NOT NULL | Last update timestamp |
