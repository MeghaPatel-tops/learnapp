import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import AppLayout from '../layouts/AppLayout';
import AuthLayout from '../layouts/AuthLayout';

// Route Guards
import ProtectedRoute from './ProtectedRoute';
import PublicRoute from './PublicRoute';

// Auth Pages
import LoginPage from '../pages/auth/LoginPage';
import ForgotPasswordPage from '../pages/auth/ForgotPasswordPage';
import ResetPasswordPage from '../pages/auth/ResetPasswordPage';
import ProfilePage from '../pages/auth/ProfilePage';
import PublicVerifyPage from '../pages/certificates/PublicVerifyPage';

// Main App Pages
import DashboardPage from '../pages/dashboard/DashboardPage';
import UserListPage from '../pages/users/UserListPage';
import StudentListPage from '../pages/students/StudentListPage';
import InstructorListPage from '../pages/instructors/InstructorListPage';
import CourseListPage from '../pages/courses/CourseListPage';
import CourseDetailPage from '../pages/courses/CourseDetailPage';
import BatchListPage from '../pages/batches/BatchListPage';
import BatchDetailPage from '../pages/batches/BatchDetailPage';
import EnrollmentListPage from '../pages/enrollments/EnrollmentListPage';
import AssignmentListPage from '../pages/assignments/AssignmentListPage';
import SubmissionListPage from '../pages/assignments/SubmissionListPage';
import QuizListPage from '../pages/quizzes/QuizListPage';
import QuizRunnerPage from '../pages/quizzes/QuizRunnerPage';
import AttendancePage from '../pages/attendance/AttendancePage';
import PaymentListPage from '../pages/payments/PaymentListPage';
import CertificateListPage from '../pages/certificates/CertificateListPage';
import AnnouncementListPage from '../pages/announcements/AnnouncementListPage';
import ReportExportPage from '../pages/reports/ReportExportPage';

import { ROLES } from '../utils/constants';

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public Certificate Verification (Accessible with or without login) */}
      <Route path="/verify-certificate" element={<PublicVerifyPage />} />
      <Route path="/verify-certificate/:code" element={<PublicVerifyPage />} />

      {/* Guest Authentication Routes */}
      <Route element={<PublicRoute />}>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Route>
      </Route>

      {/* Authenticated Protected Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          {/* General Dashboard & Profile */}
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />

          {/* Academic Modules */}
          <Route path="/courses" element={<CourseListPage />} />
          <Route path="/courses/:id" element={<CourseDetailPage />} />
          <Route path="/batches" element={<BatchListPage />} />
          <Route path="/batches/:id" element={<BatchDetailPage />} />
          <Route path="/enrollments" element={<EnrollmentListPage />} />

          {/* Assessments & Content */}
          <Route path="/assignments" element={<AssignmentListPage />} />
          <Route path="/submissions" element={<SubmissionListPage />} />
          <Route path="/quizzes" element={<QuizListPage />} />
          <Route
            path="/quizzes/:quizId/runner/:attemptId"
            element={<QuizRunnerPage />}
          />

          {/* Operations */}
          <Route path="/attendance" element={<AttendancePage />} />
          <Route path="/announcements" element={<AnnouncementListPage />} />

          {/* Student & Faculty Directory */}
          <Route
            path="/students"
            element={
              <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.INSTRUCTOR]} />
            }
          >
            <Route index element={<StudentListPage />} />
          </Route>

          <Route path="/instructors" element={<InstructorListPage />} />

          {/* Financials & Certification */}
          <Route
            path="/payments"
            element={
              <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.STUDENT]} />
            }
          >
            <Route index element={<PaymentListPage />} />
          </Route>

          <Route
            path="/certificates"
            element={
              <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.STUDENT]} />
            }
          >
            <Route index element={<CertificateListPage />} />
          </Route>

          {/* Admin Exclusive: User Directory */}
          <Route
            path="/users"
            element={<ProtectedRoute allowedRoles={[ROLES.ADMIN]} />}
          >
            <Route index element={<UserListPage />} />
          </Route>

          {/* Reporting: Admin and Instructor */}
          <Route
            path="/reports"
            element={
              <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.INSTRUCTOR]} />
            }
          >
            <Route index element={<ReportExportPage />} />
          </Route>
        </Route>
      </Route>

      {/* Fallback Redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
