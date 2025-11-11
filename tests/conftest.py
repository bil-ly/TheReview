import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import FastAPI

from app.main import app as main_app
from app.core.auth.auth_setup import create_auth_service
from app.core.config import settings


# MongoDB Test Database Configuration
TEST_MONGODB_URL = "mongodb://localhost:27017"
TEST_DATABASE_NAME = "test_the_review_users"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Create a test database for each test function.
    Drops the database after the test completes.
    """
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    db = client[TEST_DATABASE_NAME]

    yield db

    # Cleanup: drop the test database after each test
    await client.drop_database(TEST_DATABASE_NAME)
    client.close()


@pytest.fixture(scope="function")
async def app(test_db: AsyncIOMotorDatabase) -> FastAPI:
    """
    Create a FastAPI app instance with test database for each test.
    """
    # Create a new app instance
    test_app = main_app

    # Initialize auth service with test database
    test_app.state.auth_service = create_auth_service(test_db)

    return test_app


@pytest.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def sample_user_data():
    """Sample user data for registration tests."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "SecureP@ssw0rd123!"
    }


@pytest.fixture
def sample_user_data_2():
    """Another sample user data for testing."""
    return {
        "username": "anotheruser",
        "email": "another@example.com",
        "full_name": "Another User",
        "password": "AnotherP@ss123!"
    }


@pytest.fixture
async def registered_user(client: AsyncClient, sample_user_data):
    """
    Fixture that registers a user and returns the registration response and user data.
    """
    response = await client.post("/auth/register", json=sample_user_data)
    assert response.status_code == 200
    return {
        "user_data": sample_user_data,
        "response": response.json()
    }


@pytest.fixture
async def authenticated_user(client: AsyncClient, registered_user):
    """
    Fixture that registers and logs in a user, returning the auth token.
    """
    user_data = registered_user["user_data"]
    login_response = await client.post(
        "/auth/login",
        json={
            "username": user_data["username"],
            "password": user_data["password"]
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()

    return {
        "user_data": user_data,
        "token": token_data["access_token"],
        "token_type": token_data["token_type"]
    }
