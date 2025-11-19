# TheReview Backend - Docker Setup

## 🚀 Quick Start (3 Commands)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start everything
make dev-up

# 3. Run migrations
make db-migrate
```

**Done!** Your API is running at http://localhost:8000

---

## 📦 What's Included?

### Services

| Service | Port | Purpose | UI |
|---------|------|---------|-----|
| **FastAPI** | 8000 | Backend API | http://localhost:8000 |
| **PostgreSQL** | 5432 | Review data | - |
| **MongoDB** | 27017 | User data | - |
| **Redis** | 6379 | Caching | - |
| **PgAdmin** | 5050 | PostgreSQL UI | http://localhost:5050 |
| **Mongo Express** | 8081 | MongoDB UI | http://localhost:8081 |
| **Redis Commander** | 8082 | Redis UI | http://localhost:8082 |

### Admin Tools (Optional)

```bash
# Start with admin UIs
make dev-up-tools
```

---

## 🎯 Common Commands

### Development

```bash
make dev-up           # Start all services
make dev-down         # Stop all services
make dev-logs         # View all logs
make dev-logs-api     # View API logs only
make dev-restart      # Restart services
make dev-shell        # Open shell in API container
make dev-ps           # Show container status
```

### Database

```bash
make db-migrate       # Run migrations
make db-status        # Check migration status
make db-psql          # PostgreSQL shell
make db-mongo         # MongoDB shell
make db-redis         # Redis CLI
```

### Testing

```bash
make test             # Run tests
make test-cov         # Tests with coverage
make lint             # Check code quality
make lint-fix         # Fix linting issues
```

### Utilities

```bash
make health           # Check service health
make stats            # Resource usage
make backup-postgres  # Backup database
make clean            # Clean up Docker
```

---

## 🏭 Production Deployment

### Build & Deploy

```bash
# Build production image
make build-prod

# Start production stack
make prod-up

# Scale to 3 instances
make prod-scale n=3

# Deploy updates
make prod-deploy

# View logs
make prod-logs
```

### With Monitoring

```bash
# Start with Prometheus & Grafana
make prod-up-monitoring

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

---

## 🔐 Environment Configuration

### Development (.env)

```env
# Quick setup for development
POSTGRES_PASSWORD=postgres
JWT_SECRET_KEY=dev_secret_key
```

### Production (.env.prod)

```env
# IMPORTANT: Use strong secrets!
POSTGRES_PASSWORD=<generate-strong-password>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
REDIS_PASSWORD=<generate-strong-password>
```

**Generate Strong Secrets:**

```bash
# JWT Secret
openssl rand -hex 32

# Passwords
openssl rand -base64 32
```

---

## 📊 Health Checks

### Check All Services

```bash
make health
```

### Manual Checks

```bash
# API Health
curl http://localhost:8000/health

# Detailed Health
curl http://localhost:8000/health/ready | jq

# Liveness
curl http://localhost:8000/health/live | jq
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
make dev-logs

# Check specific service
docker-compose logs postgres

# Verify ports aren't in use
lsof -i :8000
lsof -i :5432
```

### Database Connection Issues

```bash
# Check PostgreSQL
make db-psql

# Check MongoDB
make db-mongo

# Check Redis
make db-redis
```

### Reset Everything

```bash
# Stop and remove data (DESTRUCTIVE!)
make dev-down-clean

# Start fresh
make dev-up
make db-migrate
```

---

## 📁 Project Structure

```
backend/
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # Development
├── docker-compose.prod.yml     # Production
├── docker-entrypoint.sh        # Startup script
├── Makefile                    # Commands
├── .dockerignore               # Build exclusions
├── .env.example                # Config template
│
├── app/                        # Application code
├── alembic/                    # Migrations
├── tests/                      # Test suite
│
└── docker/                     # Optional configs
    ├── nginx/
    ├── postgres/
    └── prometheus/
```

---

## 🏗️ Docker Architecture

### Multi-Stage Build

```
Stage 1: base          → Security-hardened base (~200MB)
Stage 2: builder       → Install dependencies (~800MB)
Stage 3: development   → Dev tools + hot reload (~600MB)
Stage 4: production    → Minimal runtime (~400MB) ✓
```

### Build Targets

```bash
# Development (with dev tools)
docker build --target development -t thereview:dev .

# Production (minimal)
docker build --target production -t thereview:prod .
```

---

## 🔒 Security Features

✅ **Non-root user** (UID 1001)
✅ **Multi-stage builds** (smaller attack surface)
✅ **Health checks** (automatic recovery)
✅ **Resource limits** (prevent resource exhaustion)
✅ **Secret management** (Docker secrets support)
✅ **Read-only filesystem** (optional)
✅ **Security scanning** (Trivy, Snyk compatible)
✅ **Log rotation** (prevent disk fill)

---

## 📈 Performance Optimizations

- **Layer caching**: Dependencies cached separately
- **BuildKit**: Parallel builds enabled
- **Connection pooling**: PostgreSQL (10+20), Redis (10)
- **Resource limits**: CPU and memory constraints
- **Hot reload**: Development only (volumes)
- **Multi-replica**: Production scaling

---

## 🌐 Networking

### Service Discovery

Services communicate by name:

```python
POSTGRES_HOST=postgres      # Not localhost!
MONGODB_URL=mongodb://mongodb:27017/
REDIS_HOST=redis://redis:6379
```

### Network Diagram

```
┌───────────────────────────────────┐
│     thereview-network (bridge)    │
├───────────────────────────────────┤
│  api ←→ postgres                  │
│  api ←→ mongodb                   │
│  api ←→ redis                     │
│  nginx ←→ api                     │
└───────────────────────────────────┘
```

---

## 💾 Data Persistence

### Volumes

```bash
# List volumes
docker volume ls | grep thereview

# Inspect volume
docker volume inspect thereview-postgres-dev-data

# Backup volume
docker run --rm -v thereview-postgres-dev-data:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/postgres.tar.gz /data
```

### Backups

```bash
# Backup PostgreSQL
make backup-postgres

# Backup MongoDB
make backup-mongodb

# Restore PostgreSQL
make restore-postgres file=backups/postgres_20240101_120000.sql
```

---

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
- name: Build and test
  run: |
    docker-compose up -d
    make test

- name: Build production
  run: make build-prod

- name: Push to registry
  run: docker push thereview/backend:latest
```

### GitLab CI

```yaml
build:
  script:
    - docker-compose up -d
    - make test
    - make build-prod
```

---

## 📚 Documentation

- **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** - Complete Docker guide
- **[DATABASE_SETUP.md](DATABASE_SETUP.md)** - Database setup
- **[CACHING_GUIDE.md](CACHING_GUIDE.md)** - Caching strategies
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Architecture overview

---

## 🆘 Need Help?

### Check These First

1. **Logs**: `make dev-logs`
2. **Health**: `make health`
3. **Status**: `make dev-ps`
4. **Stats**: `make stats`

### Common Issues

| Issue | Solution |
|-------|----------|
| Port already in use | `lsof -i :8000` and kill process |
| Database won't connect | `make db-psql` to test |
| Container keeps restarting | `make dev-logs` for errors |
| Out of disk space | `make clean` to free space |

---

## 🎉 Success Checklist

After running `make dev-up`:

- [ ] API responds at http://localhost:8000/health
- [ ] Swagger docs at http://localhost:8000/docs
- [ ] PgAdmin accessible (if tools enabled)
- [ ] Migrations ran successfully
- [ ] Tests pass: `make test`
- [ ] Can connect to databases

---

**You're all set! Happy coding! 🚀**

For detailed documentation, see [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
