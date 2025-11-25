# CI Services Configuration

## Overview

The CI pipelines require **MongoDB** and **Redis** services to run tests successfully. These are configured as GitHub Actions service containers.

## Services

### MongoDB
- **Image**: `mongo:7.0`
- **Port**: 27017
- **Purpose**: Database for user authentication and data storage
- **Health Check**: Runs `mongosh --eval 'db.runCommand({ ping: 1 })'` every 10 seconds

### Redis
- **Image**: `redis:7-alpine`
- **Port**: 6379
- **Purpose**: Session management and 2FA token storage
- **Health Check**: Runs `redis-cli ping` every 10 seconds


## Local vs CI

### Running Tests Locally

When you run tests locally, you need MongoDB and Redis running:

```bash
# Option 1: Using Docker Compose (recommended)
docker-compose up -d mongodb redis

# Option 2: Using individual Docker containers
docker run -d -p 27017:27017 mongo:7.0
docker run -d -p 6379:6379 redis:7-alpine

# Option 3: Installed natively
# MongoDB and Redis installed on your system

# Then run tests
uv run pytest -v
```

### Running Tests in CI

GitHub Actions automatically:
1. Starts MongoDB and Redis containers
2. Waits for health checks to pass
3. Runs tests
4. Shuts down containers

No manual setup needed!

## Verifying Services in CI

You can add a verification step to your workflow to confirm services are running:

```yaml
- name: Verify services are running
  run: |
    echo "Checking MongoDB..."
    mongosh --eval "db.runCommand({ ping: 1 })"

    echo "Checking Redis..."
    redis-cli ping
```

## Service Configuration Details

### MongoDB Configuration
```yaml
services:
  mongodb:
    image: mongo:7.0
    ports:
      - 27017:27017
    options: >-
      --health-cmd "mongosh --eval 'db.runCommand({ ping: 1 })'"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### Redis Configuration
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

## Troubleshooting

### Tests still failing with connection errors?

1. **Check service health**
   - Look for "Service container mongodb started" in CI logs
   - Look for "Service container redis started" in CI logs

2. **Check connection strings**
   - Tests should use `mongodb://localhost:27017`
   - Redis should connect to `localhost:6379`
   - GitHub Actions runs on `ubuntu-latest` where `localhost` works correctly

3. **Check health checks**
   - Services wait for health checks before tests run
   - If health checks fail, services may not be ready

### Different ports in tests?

Update `tests/conftest.py`:
```python
TEST_MONGODB_URL = "mongodb://localhost:27017"  # Must match service port
```

### Need authentication for MongoDB/Redis?

Add environment variables to the service:
```yaml
services:
  mongodb:
    image: mongo:7.0
    env:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - 27017:27017
```

Then update connection string:
```python
TEST_MONGODB_URL = "mongodb://admin:password@localhost:27017"
```

## Performance

Service containers:
-  Start in parallel with job setup (~10-15 seconds)
-  Use Docker layer caching for faster startup
-  Automatically cleaned up after job completes
-  No cost impact (included in GitHub Actions free tier)

## Security

- Services run in isolated containers
- Only accessible within the job
- Destroyed after job completes
- No persistent data between runs
- No external network access

## Summary

 MongoDB and Redis now run automatically in CI
 Tests pass in both local and CI environments
 Health checks ensure services are ready
 No manual configuration needed
 Fast and reliable test execution
