"""Tests for Dashboard, Notifications, Announcements, Reports, and RBAC."""

import pytest
from tests.conftest import create_test_user


class TestDashboard:
    def test_admin_dashboard(self, client, admin_headers):
        resp = client.get("/api/dashboard", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_students" in data
        assert "total_revenue" in data

    def test_student_dashboard(self, client, student_headers):
        resp = client.get("/api/dashboard", headers=student_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "enrolled_courses" in data
        assert "pending_assignments" in data

    def test_instructor_dashboard(self, client, instructor_headers):
        resp = client.get("/api/dashboard", headers=instructor_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "assigned_courses" in data
        assert "pending_evaluations" in data

    def test_no_auth(self, client):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 401


class TestNotifications:
    def test_list_empty(self, client, admin_headers):
        resp = client.get("/api/notifications", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_mark_all_read(self, client, admin_headers):
        resp = client.post("/api/notifications/read-all", headers=admin_headers)
        assert resp.status_code == 200

    def test_mark_nonexistent_404(self, client, admin_headers):
        resp = client.patch("/api/notifications/99999/read", headers=admin_headers)
        assert resp.status_code == 404


class TestAnnouncements:
    def test_create_announcement(self, client, admin_headers):
        resp = client.post(
            "/api/announcements",
            json={"title": "Welcome", "content": "Welcome to the LMS platform!"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Welcome"

    def test_list_announcements(self, client, admin_headers):
        client.post(
            "/api/announcements",
            json={"title": "Notice", "content": "Important notice for all users."},
            headers=admin_headers,
        )
        resp = client.get("/api/announcements", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_student_cannot_create_announcement(self, client, student_headers):
        resp = client.post(
            "/api/announcements",
            json={"title": "X", "content": "Y" * 10},
            headers=student_headers,
        )
        assert resp.status_code == 403


class TestReports:
    def test_students_csv(self, client, admin_headers):
        resp = client.get("/api/reports/students?format=csv", headers=admin_headers)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    def test_enrollments_xlsx(self, client, admin_headers):
        resp = client.get("/api/reports/enrollments?format=xlsx", headers=admin_headers)
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    def test_payments_pdf(self, client, admin_headers):
        resp = client.get("/api/reports/payments?format=pdf", headers=admin_headers)
        assert resp.status_code == 200
        assert "application/pdf" in resp.headers["content-type"]

    def test_invalid_report_type(self, client, admin_headers):
        resp = client.get("/api/reports/invalid-type", headers=admin_headers)
        assert resp.status_code == 400

    def test_student_cannot_export(self, client, student_headers):
        resp = client.get("/api/reports/students", headers=student_headers)
        assert resp.status_code == 403


class TestRBAC:
    """Cross-role access denial tests."""

    def test_student_cannot_manage_users(self, client, student_headers):
        assert client.get("/api/users", headers=student_headers).status_code == 403

    def test_student_cannot_create_course(self, client, student_headers):
        assert client.post("/api/courses", json={}, headers=student_headers).status_code == 403

    def test_student_cannot_create_batch(self, client, student_headers):
        assert client.post("/api/batches", json={}, headers=student_headers).status_code == 403

    def test_student_cannot_record_payment(self, client, student_headers):
        assert client.post("/api/payments", json={}, headers=student_headers).status_code == 403

    def test_instructor_cannot_manage_users(self, client, instructor_headers):
        assert client.get("/api/users", headers=instructor_headers).status_code == 403

    def test_instructor_cannot_create_enrollment(self, client, instructor_headers):
        assert client.post("/api/enrollments", json={}, headers=instructor_headers).status_code == 403

    def test_unauthenticated_access(self, client):
        for path in ["/api/courses", "/api/batches", "/api/users", "/api/payments", "/api/dashboard"]:
            assert client.get(path).status_code == 401

    def test_certificate_verify_is_public(self, client):
        resp = client.get("/api/certificates/verify/NONEXISTENT")
        # 404 is expected (no cert), but NOT 401 – the endpoint is public
        assert resp.status_code == 404
