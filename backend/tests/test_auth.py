from datetime import timedelta
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


def get_random_email() -> str:
    """Generate isolated unique test email addresses."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


class TestRegistration:
    def test_successful_registration(self):
        email = get_random_email()
        payload = {
            "name": "Alex Candidate",
            "email": email,
            "password": "SecurePassword123"
        }
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email.lower()
        assert data["name"] == "Alex Candidate"
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data

    def test_duplicate_email_rejection(self):
        email = get_random_email()
        payload = {
            "name": "Alex Candidate",
            "email": email,
            "password": "SecurePassword123"
        }
        res1 = client.post("/api/auth/register", json=payload)
        assert res1.status_code == 201

        # Attempt to register with the same email
        res2 = client.post("/api/auth/register", json=payload)
        assert res2.status_code == 409
        assert "already exists" in res2.json()["detail"].lower()

    def test_invalid_email_format(self):
        payload = {
            "name": "Invalid Email User",
            "email": "not-an-email",
            "password": "SecurePassword123"
        }
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 422

    def test_short_password_rejected(self):
        payload = {
            "name": "Short Password User",
            "email": get_random_email(),
            "password": "123"  # Less than minimum 6 characters
        }
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self):
        email = get_random_email()
        password = "ValidPassword123"
        # Register user first
        reg_res = client.post("/api/auth/register", json={
            "name": "Login User",
            "email": email,
            "password": password
        })
        assert reg_res.status_code == 201

        # Login with correct credentials
        login_res = client.post("/api/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_res.status_code == 200
        token_data = login_res.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert len(token_data["access_token"]) > 20

    def test_login_incorrect_password(self):
        email = get_random_email()
        client.post("/api/auth/register", json={
            "name": "Login User",
            "email": email,
            "password": "CorrectPassword123"
        })

        login_res = client.post("/api/auth/login", json={
            "email": email,
            "password": "WrongPassword456"
        })
        assert login_res.status_code == 401
        assert "Invalid email or password" in login_res.json()["detail"]

    def test_login_unknown_email(self):
        login_res = client.post("/api/auth/login", json={
            "email": "nonexistent_user_9999@example.com",
            "password": "SomePassword123"
        })
        assert login_res.status_code == 401
        assert "Invalid email or password" in login_res.json()["detail"]


class TestCurrentUserAndProtectedEndpoints:
    def test_get_me_with_valid_jwt(self):
        email = get_random_email()
        reg_res = client.post("/api/auth/register", json={
            "name": "Current User Test",
            "email": email,
            "password": "TestPassword123"
        })
        user_id = reg_res.json()["id"]

        login_res = client.post("/api/auth/login", json={
            "email": email,
            "password": "TestPassword123"
        })
        token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        me_res = client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        user_info = me_res.json()
        assert user_info["id"] == user_id
        assert user_info["email"] == email.lower()
        assert user_info["name"] == "Current User Test"
        assert "password_hash" not in user_info

    def test_get_me_missing_token(self):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self):
        headers = {"Authorization": "Bearer invalid.token.string"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401

    def test_get_me_expired_token(self):
        # Create an expired token manually using negative expires_delta
        expired_token = create_access_token(
            data={"sub": "1"},
            expires_delta=timedelta(minutes=-10)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_protected_test_endpoint_without_token(self):
        response = client.get("/api/auth/protected-test")
        assert response.status_code == 401

    def test_protected_test_endpoint_with_valid_token(self):
        email = get_random_email()
        reg_res = client.post("/api/auth/register", json={
            "name": "Protected Test User",
            "email": email,
            "password": "TestPassword123"
        })
        user_id = reg_res.json()["id"]

        login_res = client.post("/api/auth/login", json={
            "email": email,
            "password": "TestPassword123"
        })
        token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/protected-test", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Authentication successful"
        assert data["user_id"] == user_id
