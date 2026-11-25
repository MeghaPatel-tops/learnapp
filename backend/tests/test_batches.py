"""Tests for Batch, Enrollment, and Payment endpoints."""

import pytest
from tests.conftest import create_test_user

COURSE_PAYLOAD = {
    "course_code": "BATCH-C01",
    "name": "Batch Test Course",
    "description": "Course for batch testing scenarios.",
    "category": "Testing",
    "duration_hours": 20,
    "fee": "3000.00",
}


def _setup_published_course(client, admin_headers):
    """Create and publish a course, return its id."""
    c = client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers).json()
    client.post(f"/api/courses/{c['id']}/publish", headers=admin_headers)
    return c["id"]


class TestBatchCRUD:
    def test_create_batch(self, client, admin_headers, instructor_user, db):
        from app.models.user import Instructor
        from sqlalchemy import select
        inst_user, _ = instructor_user
        inst = db.execute(select(Instructor).where(Instructor.user_id == inst_user.id)).scalar_one()
        course_id = _setup_published_course(client, admin_headers)
        payload = {
            "batch_code": "B-001",
            "name": "Morning Batch",
            "course_id": course_id,
            "instructor_id": inst.id,
            "start_date": "2027-01-10",
            "end_date": "2027-04-10",
            "class_days": "Mon,Wed,Fri",
            "class_timing": "09:00-11:00",
            "capacity": 30,
        }
        resp = client.post("/api/batches", json=payload, headers=admin_headers)
        assert resp.status_code == 201
        assert resp.json()["batch_code"] == "B-001"

    def test_student_cannot_create_batch(self, client, student_headers):
        resp = client.post("/api/batches", json={}, headers=student_headers)
        assert resp.status_code == 403


class TestEnrollments:
    def test_create_enrollment(self, client, admin_headers, student_user):
        student, _ = student_user
        course_id = _setup_published_course(client, admin_headers)
        resp = client.post(
            "/api/enrollments",
            json={"student_id": student.id, "course_id": course_id},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "active"

    def test_duplicate_enrollment_rejected(self, client, admin_headers, student_user):
        student, _ = student_user
        course_id = _setup_published_course(client, admin_headers)
        client.post(
            "/api/enrollments",
            json={"student_id": student.id, "course_id": course_id},
            headers=admin_headers,
        )
        dup = client.post(
            "/api/enrollments",
            json={"student_id": student.id, "course_id": course_id},
            headers=admin_headers,
        )
        assert dup.status_code == 409


class TestPayments:
    def _enroll_and_get_id(self, client, admin_headers, student_user):
        student, _ = student_user
        course_id = _setup_published_course(client, admin_headers)
        enr = client.post(
            "/api/enrollments",
            json={"student_id": student.id, "course_id": course_id},
            headers=admin_headers,
        ).json()
        return enr["id"]

    def test_create_payment(self, client, admin_headers, student_user):
        enr_id = self._enroll_and_get_id(client, admin_headers, student_user)
        resp = client.post(
            "/api/payments",
            json={"enrollment_id": enr_id, "amount_paid": "1000.00", "payment_method": "cash"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "partially_paid"

    def test_full_payment(self, client, admin_headers, student_user):
        enr_id = self._enroll_and_get_id(client, admin_headers, student_user)
        resp = client.post(
            "/api/payments",
            json={"enrollment_id": enr_id, "amount_paid": "3000.00", "payment_method": "card"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "paid"

    def test_overpayment_rejected(self, client, admin_headers, student_user):
        enr_id = self._enroll_and_get_id(client, admin_headers, student_user)
        resp = client.post(
            "/api/payments",
            json={"enrollment_id": enr_id, "amount_paid": "9999.00", "payment_method": "cash"},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "OVERPAYMENT"

    def test_list_payments(self, client, admin_headers):
        resp = client.get("/api/payments", headers=admin_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()
