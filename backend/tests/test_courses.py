"""Tests for Course and Module CRUD endpoints."""

import pytest
from tests.conftest import create_test_user

COURSE_PAYLOAD = {
    "course_code": "CS101",
    "name": "Intro to CS",
    "description": "An introductory course to computer science.",
    "category": "Technology",
    "duration_hours": 40,
    "fee": "5000.00",
}


class TestCourseCRUD:
    def test_create_course(self, client, admin_headers):
        resp = client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["course_code"] == "CS101"
        assert data["status"] == "draft"

    def test_list_courses(self, client, admin_headers):
        client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers)
        resp = client.get("/api/courses", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_course(self, client, admin_headers):
        create_resp = client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers)
        cid = create_resp.json()["id"]
        resp = client.get(f"/api/courses/{cid}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == cid

    def test_update_course(self, client, admin_headers):
        create_resp = client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers)
        cid = create_resp.json()["id"]
        resp = client.put(f"/api/courses/{cid}", json={"name": "Advanced CS"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Advanced CS"

    def test_publish_and_archive(self, client, admin_headers):
        create_resp = client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers)
        cid = create_resp.json()["id"]
        pub = client.post(f"/api/courses/{cid}/publish", headers=admin_headers)
        assert pub.status_code == 200
        assert pub.json()["status"] == "published"
        arch = client.post(f"/api/courses/{cid}/archive", headers=admin_headers)
        assert arch.status_code == 200
        assert arch.json()["status"] == "archived"

    def test_delete_course(self, client, admin_headers):
        create_resp = client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers)
        cid = create_resp.json()["id"]
        resp = client.delete(f"/api/courses/{cid}", headers=admin_headers)
        assert resp.status_code == 204

    def test_student_cannot_create_course(self, client, student_headers):
        resp = client.post("/api/courses", json=COURSE_PAYLOAD, headers=student_headers)
        assert resp.status_code == 403


class TestModuleCRUD:
    def test_create_and_list_modules(self, client, admin_headers):
        course = client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers).json()
        cid = course["id"]
        mod_resp = client.post(
            f"/api/courses/{cid}/modules",
            json={"title": "Module 1", "sequence_order": 1},
            headers=admin_headers,
        )
        assert mod_resp.status_code == 201
        mods = client.get(f"/api/courses/{cid}/modules", headers=admin_headers)
        assert mods.status_code == 200
        assert len(mods.json()) >= 1

    def test_update_module(self, client, admin_headers):
        course = client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers).json()
        cid = course["id"]
        mod = client.post(
            f"/api/courses/{cid}/modules",
            json={"title": "M1", "sequence_order": 1},
            headers=admin_headers,
        ).json()
        resp = client.put(
            f"/api/courses/{cid}/modules/{mod['id']}",
            json={"title": "Updated Module"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Module"

    def test_delete_module(self, client, admin_headers):
        course = client.post("/api/courses", json=COURSE_PAYLOAD, headers=admin_headers).json()
        cid = course["id"]
        mod = client.post(
            f"/api/courses/{cid}/modules",
            json={"title": "M1", "sequence_order": 1},
            headers=admin_headers,
        ).json()
        resp = client.delete(f"/api/courses/{cid}/modules/{mod['id']}", headers=admin_headers)
        assert resp.status_code == 200
