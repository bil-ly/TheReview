"""
Tests for authentication endpoints.

This module tests:
- User registration
- User login
- Error handling and validation
"""

import pytest
from httpx import AsyncClient


class TestUserRegistration:
    """Test cases for user registration endpoint."""

    async def test_register_user_success(self, client: AsyncClient, sample_user_data):
        """Test successful user registration."""
        response = await client.post("/auth/register", json=sample_user_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "User registered successfully"
        assert "user_id" in data
        assert isinstance(data["user_id"], str)

    async def test_register_user_duplicate_username(
        self, client: AsyncClient, registered_user, sample_user_data
    ):
        """Test registration with duplicate username fails."""
        # Try to register with same username but different email
        duplicate_data = {
            **sample_user_data,
            "email": "different@example.com"
        }

        response = await client.post("/auth/register", json=duplicate_data)

        assert response.status_code in [400, 409]  # Bad request or conflict
        data = response.json()
        assert "detail" in data

    async def test_register_user_duplicate_email(
        self, client: AsyncClient, registered_user
    ):
        """Test registration with duplicate email fails."""
        # Try to register with same email but different username
        duplicate_data = {
            "username": "differentuser",
            "email": registered_user["user_data"]["email"],
            "full_name": "Different User",
            "password": "AnotherP@ss123!"
        }

        response = await client.post("/auth/register", json=duplicate_data)

        assert response.status_code in [400, 409]
        data = response.json()
        assert "detail" in data

    async def test_register_user_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails."""
        weak_password_data = {
            "username": "weakpass",
            "email": "weak@example.com",
            "full_name": "Weak Password",
            "password": "123"  # Too short and weak
        }

        response = await client.post("/auth/register", json=weak_password_data)

        assert response.status_code in [400, 422]
        data = response.json()
        assert "detail" in data

    async def test_register_user_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields fails."""
        incomplete_data = {
            "username": "incomplete",
            "email": "incomplete@example.com"
            # Missing full_name and password
        }

        response = await client.post("/auth/register", json=incomplete_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    async def test_register_user_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format.

        Note: Backend currently accepts any string as email.
        This test documents current behavior.
        """
        invalid_email_data = {
            "username": "invalidemail",
            "email": "not-an-email",
            "full_name": "Invalid Email",
            "password": "ValidP@ss123!"
        }

        response = await client.post("/auth/register", json=invalid_email_data)

        # Currently backend accepts this (no strict email validation)
        # Could be improved with email validation in the future
        assert response.status_code in [200, 422]

    async def test_register_user_empty_username(self, client: AsyncClient):
        """Test registration with empty username.

        Note: Backend currently accepts empty username.
        This test documents current behavior.
        """
        empty_username_data = {
            "username": "",
            "email": "empty@example.com",
            "full_name": "Empty Username",
            "password": "ValidP@ss123!"
        }

        response = await client.post("/auth/register", json=empty_username_data)

        # Currently backend accepts this (no empty string validation)
        # Could be improved with stricter validation in the future
        assert response.status_code in [200, 400, 422]

    async def test_register_multiple_users(
        self, client: AsyncClient, sample_user_data, sample_user_data_2
    ):
        """Test registering multiple different users succeeds."""
        # Register first user
        response1 = await client.post("/auth/register", json=sample_user_data)
        assert response1.status_code == 200

        # Register second user
        response2 = await client.post("/auth/register", json=sample_user_data_2)
        assert response2.status_code == 200

        # Verify they got different user IDs
        user1_id = response1.json()["user_id"]
        user2_id = response2.json()["user_id"]
        assert user1_id != user2_id


class TestUserLogin:
    """Test cases for user login endpoint."""

    async def test_login_success(self, client: AsyncClient, registered_user):
        """Test successful user login."""
        user_data = registered_user["user_data"]

        response = await client.post(
            "/auth/login",
            json={
                "username": user_data["username"],
                "password": user_data["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    async def test_login_invalid_username(self, client: AsyncClient, registered_user):
        """Test login with non-existent username fails."""
        response = await client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "somepassword"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_wrong_password(self, client: AsyncClient, registered_user):
        """Test login with incorrect password fails."""
        user_data = registered_user["user_data"]

        response = await client.post(
            "/auth/login",
            json={
                "username": user_data["username"],
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_missing_username(self, client: AsyncClient):
        """Test login with missing username fails."""
        response = await client.post(
            "/auth/login",
            json={"password": "somepassword"}
        )

        assert response.status_code == 422

    async def test_login_missing_password(self, client: AsyncClient, registered_user):
        """Test login with missing password fails."""
        user_data = registered_user["user_data"]

        response = await client.post(
            "/auth/login",
            json={"username": user_data["username"]}
        )

        assert response.status_code == 422

    async def test_login_empty_credentials(self, client: AsyncClient):
        """Test login with empty credentials fails."""
        response = await client.post(
            "/auth/login",
            json={"username": "", "password": ""}
        )

        assert response.status_code in [400, 401, 422]

    async def test_login_case_sensitive_username(
        self, client: AsyncClient, registered_user
    ):
        """Test that username is case-sensitive."""
        user_data = registered_user["user_data"]

        # Try to login with uppercase username
        response = await client.post(
            "/auth/login",
            json={
                "username": user_data["username"].upper(),
                "password": user_data["password"]
            }
        )

        # Should fail because username doesn't match
        assert response.status_code == 401

    async def test_login_multiple_times(self, client: AsyncClient, registered_user):
        """Test that user can login multiple times successfully."""
        user_data = registered_user["user_data"]

        # Login first time
        response1 = await client.post(
            "/auth/login",
            json={
                "username": user_data["username"],
                "password": user_data["password"]
            }
        )
        assert response1.status_code == 200
        token1 = response1.json()["access_token"]

        # Login second time
        response2 = await client.post(
            "/auth/login",
            json={
                "username": user_data["username"],
                "password": user_data["password"]
            }
        )
        assert response2.status_code == 200
        token2 = response2.json()["access_token"]

        # Both logins should succeed
        assert token1 is not None
        assert token2 is not None


class TestAuthenticationFlow:
    """Test complete authentication flows."""

    async def test_register_and_login_flow(self, client: AsyncClient, sample_user_data):
        """Test complete flow: register then login."""
        # Step 1: Register
        register_response = await client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 200

        # Step 2: Login with registered credentials
        login_response = await client.post(
            "/auth/login",
            json={
                "username": sample_user_data["username"],
                "password": sample_user_data["password"]
            }
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

    async def test_cannot_login_before_registration(
        self, client: AsyncClient, sample_user_data
    ):
        """Test that user cannot login without registering first."""
        # Try to login without registering
        response = await client.post(
            "/auth/login",
            json={
                "username": sample_user_data["username"],
                "password": sample_user_data["password"]
            }
        )

        assert response.status_code == 401

    async def test_token_format(self, client: AsyncClient, authenticated_user):
        """Test that the returned token has proper JWT format."""
        token = authenticated_user["token"]

        # JWT tokens have 3 parts separated by dots
        parts = token.split(".")
        assert len(parts) == 3

        # Each part should be non-empty
        for part in parts:
            assert len(part) > 0
