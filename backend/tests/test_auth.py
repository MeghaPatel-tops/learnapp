"""Tests for authentication & user management endpoints."""

import pytest
from tests.conftest import auth_header, create_test_user


class TestLogin:
    def test_login_success(self, client, admin_user):
        user, pw = admin_user
        resp = client.post("/api/auth/login", json={"email": user.email, "password": pw})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == user.email
        assert data["user"]["role"] == "admin"

    def test_login_wrong_password(self, client, admin_user):
        user, _ = admin_user
        resp = client.post("/api/auth/login", json={"email": user.email, "password": "Wrong@9999"})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_nonexistent_email(self, client):
        resp = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "Test@12345"})
        assert resp.status_code == 401

    def test_login_inactive_user(self, client, db):
        user, pw = create_test_user(db, email="inactive@example.com", role_name="admin")
        user.is_active = False
        db.commit()
        resp = client.post("/api/auth/login", json={"email": user.email, "password": pw})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "ACCOUNT_INACTIVE"


class TestMe:
    def test_get_me(self, client, admin_headers, admin_user):
        resp = client.get("/api/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == admin_user[0].email

    def test_get_me_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


class TestRegister:
    def test_admin_can_register_student(self, client, admin_headers):
        payload = {
            "full_name": "New Student",
            "email": "new-student@example.com",
            "password": "Student@123",
            "role": "student",
            "student_code": "STU-NEW01",
        }
        resp = client.post("/api/auth/register", json=payload, headers=admin_headers)
        assert resp.status_code == 201
        assert resp.json()["role"] == "student"

    def test_student_cannot_register(self, client, student_headers):
        payload = {
            "full_name": "Hacker",
            "email": "hacker@example.com",
            "password": "Hacker@123",
            "role": "student",
        }
        resp = client.post("/api/auth/register", json=payload, headers=student_headers)
        assert resp.status_code == 403

    def test_duplicate_email_rejected(self, client, admin_headers, admin_user):
        payload = {
            "full_name": "Dup",
            "email": admin_user[0].email,
            "password": "Dup@12345",
            "role": "admin",
        }
        resp = client.post("/api/auth/register", json=payload, headers=admin_headers)
        assert resp.status_code == 409

    def test_weak_password_rejected(self, client, admin_headers):
        payload = {
            "full_name": "Weak",
            "email": "weak@example.com",
            "password": "123",
            "role": "student",
        }
        resp = client.post("/api/auth/register", json=payload, headers=admin_headers)
        assert resp.status_code == 422


class TestChangePassword:
    def test_change_password_success(self, client, admin_headers, admin_user):
        _, old_pw = admin_user
        resp = client.post(
            "/api/auth/change-password",
            json={"current_password": old_pw, "new_password": "NewPass@999"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_change_password_wrong_current(self, client, admin_headers):
        resp = client.post(
            "/api/auth/change-password",
            json={"current_password": "Wrong@9999", "new_password": "NewPass@999"},
            headers=admin_headers,
        )
        assert resp.status_code == 400
