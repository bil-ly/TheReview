# Backend Tests

This directory contains tests for TheReview backend API.

## Setup

Install test dependencies:
```bash
cd backend
uv sync --dev
```

## Running Tests

### Run all tests
```bash
uv run pytest
```

### Run specific test file
```bash
uv run pytest tests/test_authentication.py
```

### Run with verbose output
```bash
uv run pytest -v
```

### Run with coverage report
```bash
uv run pytest --cov=app --cov-report=term-missing
```

### Run specific test class or function
```bash
# Run specific test class
uv run pytest tests/test_authentication.py::TestUserRegistration -v

# Run specific test function
uv run pytest tests/test_authentication.py::TestUserRegistration::test_register_user_success -v
```

## Test Structure

- `conftest.py` - Pytest fixtures and test configuration
- `test_authentication.py` - Tests for authentication endpoints (login, register)
- `test_reviews.py` - Tests for review endpoints (placeholder)

## Test Database

Tests use a separate MongoDB database named `test_the_review_users` which is created and dropped for each test to ensure isolation.

Make sure MongoDB is running on `localhost:27017` before running tests.

## Writing New Tests

1. Create test fixtures in `conftest.py` if needed
2. Create a new test file following the naming convention `test_*.py`
3. Organize tests into classes based on functionality
4. Use descriptive test names: `test_<what>_<condition>_<expected_result>`

Example:
```python
async def test_login_success(self, client: AsyncClient, registered_user):
    """Test successful user login."""
    # Test implementation
```

## Coverage

Current test coverage:
- Authentication endpoints: 43% (login and register endpoints fully covered)
- Untested: 2FA, password reset (not yet implemented in frontend)
