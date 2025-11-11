# Testing Strategy

## Test Types

This project uses both **unit tests** and **integration tests** following the Test Pyramid pattern.

### Test Pyramid
```
        /\
       /  \      E2E Tests (Few) - Full system, browser testing
      /----\
     /      \    Integration Tests (Some) - API + Database + Services
    /--------\
   /          \  Unit Tests (Many) - Individual functions, fast
  /____________\
```

## Current Test Structure

### Integration Tests (What We Have Now)
**Location**: `tests/`
**Dependencies**: MongoDB, Redis, FastAPI
**Purpose**: Test entire features end-to-end

```
tests/
├── conftest.py                    # Fixtures with real DB/Redis
├── test_authentication.py         # INTEGRATION: Full auth flow
└── test_reviews.py               # INTEGRATION: Review operations
```

**Characteristics**:
-  Test real workflows (register → login → use API)
-  Catch integration bugs
- Verify database operations
-  Test API contracts
- Slower (need DB/Redis)
-  Can be flaky
-  Harder to debug failures

**Run**: `uv run pytest tests/`

### Unit Tests (Should Add)
**Location**: `tests/unit/` (recommended)
**Dependencies**: None (use mocks)
**Purpose**: Test individual functions in isolation

```
tests/unit/
├── test_password_utils.py         # UNIT: Password hashing/validation
├── test_jwt_utils.py              # UNIT: Token generation/validation
├── test_validators.py             # UNIT: Email, username validation
└── test_encryption.py             # UNIT: Encryption functions
```

**Characteristics**:
-  Very fast (no I/O)
-  Easy to debug
-  Test edge cases
-  High code coverage
-  Don't catch integration bugs
-  Need to mock dependencies

**Run**: `uv run pytest tests/unit/ -v --no-cov`

## Recommended Structure

### Option 1: Separate Directories (Recommended)
```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Fast, no dependencies
│   ├── conftest.py               # Unit test fixtures (mocks)
│   ├── test_password_utils.py
│   ├── test_jwt_utils.py
│   └── test_validators.py
└── integration/                   # Slow, need services
    ├── conftest.py               # Integration fixtures (real DB)
    ├── test_authentication.py
    └── test_reviews.py
```

**Run separately**:
```bash
# Fast unit tests (run often during development)
uv run pytest tests/unit/ -v

# Slower integration tests (run before commit)
uv run pytest tests/integration/ -v

# All tests (run in CI)
uv run pytest tests/ -v
```

### Option 2: Pytest Markers (Alternative)
Keep all in `tests/` but mark them:

```python
# tests/test_authentication.py
import pytest

@pytest.mark.integration
async def test_register_user_success(client):
    """Integration test - uses real DB"""
    ...

# tests/test_password_utils.py
@pytest.mark.unit
def test_hash_password():
    """Unit test - no dependencies"""
    ...
```

**Run selectively**:
```bash
# Only unit tests
uv run pytest -m unit -v

# Only integration tests
uv run pytest -m integration -v

# All tests
uv run pytest -v
```

## What Should Be Unit vs Integration?

### Good Candidates for Unit Tests
-  Password hashing/validation (`bcrypt` operations)
-  JWT token generation/parsing
-  Email validation
-  Username validation
-  Encryption/decryption functions
-  Password entropy calculation
-  Utility functions
-  Data validation (Pydantic models)

### Good Candidates for Integration Tests
-  Full authentication flow (register → login)
-  API endpoint responses
-  Database CRUD operations
-  2FA flow with Redis
-  Password reset flow with email
-  Authorization/permissions
-  Multi-step workflows

## Example: Converting to Unit Tests

### Current Integration Test
```python
# tests/test_authentication.py
async def test_register_user_success(client, sample_user_data):
    """Integration: Tests FastAPI route + DB + validation"""
    response = await client.post("/auth/register", json=sample_user_data)
    assert response.status_code == 200
```

### Extract Unit Tests
```python
# tests/unit/test_password_validation.py
from app.utils.password import calculate_entropy, hash_password, verify_password

def test_password_entropy_strong():
    """Unit: Test entropy calculation"""
    strong_password = "SecureP@ssw0rd123!"
    assert calculate_entropy(strong_password) >= 64.0

def test_password_entropy_weak():
    """Unit: Test weak password detection"""
    weak_password = "password"
    assert calculate_entropy(weak_password) < 64.0

def test_hash_password_returns_bcrypt_hash():
    """Unit: Test password hashing"""
    hashed = hash_password("mypassword")
    assert hashed.startswith("$2b$")
    assert hashed != "mypassword"

def test_verify_password_correct():
    """Unit: Test password verification"""
    password = "mypassword"
    hashed = hash_password(password)
    assert verify_password(password, hashed) == True

def test_verify_password_incorrect():
    """Unit: Test wrong password rejection"""
    hashed = hash_password("correctpass")
    assert verify_password("wrongpass", hashed) == False
```

```python
# tests/unit/test_email_validation.py
from app.utils.validators import is_valid_email

def test_valid_email():
    assert is_valid_email("user@example.com") == True
    assert is_valid_email("user.name+tag@example.co.uk") == True

def test_invalid_email():
    assert is_valid_email("invalid") == False
    assert is_valid_email("@example.com") == False
    assert is_valid_email("user@") == False
```

### Keep Integration Test
```python
# tests/integration/test_authentication.py
async def test_full_registration_flow(client, sample_user_data):
    """Integration: Test complete registration with DB"""
    # Register
    response = await client.post("/auth/register", json=sample_user_data)
    assert response.status_code == 200

    # Verify user exists in DB
    user_id = response.json()["user_id"]
    assert user_id is not None

    # Login with registered credentials
    login_response = await client.post("/auth/login", json={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"]
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
```

## CI Configuration

### Current (Integration Tests Only)
```yaml
- name: Run tests
  run: uv run pytest --cov=app --cov=lib -v
```

### Recommended (Both Types)
```yaml
- name: Run unit tests (fast)
  run: uv run pytest tests/unit/ -v --cov=app --cov=lib

- name: Run integration tests (with services)
  run: uv run pytest tests/integration/ -v --cov=app --cov=lib --cov-append
```

**Or with markers**:
```yaml
- name: Run unit tests (fast)
  run: uv run pytest -m unit -v

- name: Run integration tests (with services)
  run: uv run pytest -m integration -v
```

## Pre-Push Hook Update

Update `.githooks/pre-push` to run unit tests first (faster feedback):

```bash
# Run unit tests first (fast)
echo "Running unit tests..."
uv run pytest tests/unit/ -q || exit 1

# Then integration tests
echo "Running integration tests..."
uv run pytest tests/integration/ -q || exit 1
```

## Benefits of This Approach

### Unit Tests
-  **Fast**: Run in < 1 second
-  **Run often**: Every save during development
-  **Precise**: Pinpoint exact function that's broken
-  **Test edge cases**: Easy to test error conditions

### Integration Tests
-  **Realistic**: Test actual system behavior
-  **Catch integration bugs**: DB schema issues, API contracts
-  **Confidence**: System actually works end-to-end
-  **Coverage**: Real code paths

### Combined
-  **Fast feedback**: Unit tests catch most bugs quickly
-  **Safety net**: Integration tests catch the rest
-  **Better coverage**: Test both logic and integration
-  **Better code**: Forces you to write testable code

## Summary

Your current tests are **integration tests** because they:
-  Use real MongoDB and Redis
-  Test full API workflows
-  Require service containers in CI

**Recommendations**:
1. Keep your integration tests (they're valuable!)
2. Add unit tests for utility functions
3. Organize into `tests/unit/` and `tests/integration/`
4. Run unit tests often, integration tests before commit
5. Update CI to run both

**Naming**:
- Current: `test_authentication.py` → `integration/test_authentication.py`
- New: Create `unit/test_password_utils.py`, `unit/test_validators.py`, etc.

This gives you fast feedback during development (unit tests) and confidence before deployment (integration tests)!
