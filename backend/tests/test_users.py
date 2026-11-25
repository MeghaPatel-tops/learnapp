"""Tests for the Users admin CRUD endpoints."""


class TestListUsers:
    def test_admin_can_list(self, client, admin_headers):
        resp = client.get("/api/users", headers=admin_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_student_cannot_list(self, client, student_headers):
        resp = client.get("/api/users", headers=student_headers)
        assert resp.status_code == 403


class TestUserCRUD:
    def test_get_user_by_id(self, client, admin_headers, admin_user):
        user, _ = admin_user
        resp = client.get(f"/api/users/{user.id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == user.id

    def test_update_user(self, client, admin_headers, admin_user):
        user, _ = admin_user
        resp = client.put(
            f"/api/users/{user.id}",
            json={"full_name": "Updated Name"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    def test_deactivate_other_user(self, client, admin_headers):
        # Create a user via API so it's visible inside the same transaction
        payload = {
            "full_name": "To Deactivate",
            "email": "deactivateme@example.com",
            "password": "Deact@12345",
            "role": "student",
        }
        create_resp = client.post("/api/auth/register", json=payload, headers=admin_headers)
        assert create_resp.status_code == 201
        uid = create_resp.json()["id"]
        resp = client.delete(f"/api/users/{uid}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False
