# Docker Deployment Guide

## Overview

TheReview backend uses **multi-stage Docker builds** and **Docker Compose** for both development and production environments, following industry best practices from companies like Google, Netflix, and Uber.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Architecture                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────────┐  │
│  │   FastAPI    │   │  PostgreSQL  │   │    MongoDB    │  │
│  │   Backend    │──→│  (Reviews)   │   │    (Users)    │  │
│  │  3 replicas  │   │  Port: 5432  │   │  Port: 27017  │  │
│  │  Port: 8000  │   └──────────────┘   └───────────────┘  │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ↓                                                    │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────────┐  │
│  │    Redis     │   │    Nginx     │   │ Grafana Alloy │  │
│  │   (Cache)    │   │ (Reverse     │   │ (Monitoring)  │  │
│  │  Port: 6379  │   │   Proxy)     │   │ Ports: 12345  │  │
│  └──────────────┘   │  Port: 80    │   │  4317, 4318   │  │
│                     │  Port: 443   │   │  9090         │  │
│                     └──────────────┘   └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
backend/
├── Dockerfile                      # Multi-stage build
├── docker-entrypoint.sh            # Production startup script
├── docker-compose.yml              # Development environment
├── docker-compose.prod.yml         # Production environment
├── .dockerignore                   # Build exclusions
├── .env.example                    # Environment template
├── scripts/
│   └── generate-secrets.sh         # Secret generation script
└── docker/                         # Monitoring configs
    ├── alloy/
    │   └── config.alloy            # Grafana Alloy configuration
    └── grafana/
        └── datasources/
            └── alloy.yml           # Grafana datasource for Alloy
```

---

## 🚀 Quick Start

### Development

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. View logs
docker-compose logs -f api

# 4. Run migrations
docker-compose exec api uv run alembic upgrade head

# 5. Access services
# API: http://localhost:8000
# PgAdmin: http://localhost:5050
# Mongo Express: http://localhost:8081
# Redis Commander: http://localhost:8082
```

### Production

```bash
# 1. Set production environment variables
cp .env.example .env.prod
# Edit .env.prod with production values

# 2. Build production images
docker-compose -f docker-compose.prod.yml build

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Check health
curl http://localhost:8000/health/ready

# 5. View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

---

## 🐳 Multi-Stage Dockerfile

### Build Stages

| Stage | Purpose | Size |
|-------|---------|------|
| **base** | Security-hardened base with non-root user | ~200MB |
| **builder** | Install dependencies and compile | ~800MB |
| **development** | Dev tools + hot reload | ~600MB |
| **production** | Minimal runtime (no dev deps) | ~400MB |

### Build Commands

```bash
# Development build
docker build --target development -t thereview/backend:dev .

# Production build
docker build --target production -t thereview/backend:latest .

# Build with cache
docker build --target production \
  --cache-from thereview/backend:latest \
  -t thereview/backend:latest .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 \
  --target production \
  -t thereview/backend:latest .
```

---

## 🔧 Docker Compose Commands

### Development

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# View logs
docker-compose logs -f
docker-compose logs -f api

# Execute commands in container
docker-compose exec api bash
docker-compose exec api uv run alembic current

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove volumes (data loss!)
docker-compose down -v

# Rebuild services
docker-compose up -d --build

# Scale services
docker-compose up -d --scale api=3
```

### Production

```bash
# Use -f flag for production compose file
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml down

# Rolling update
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api
```

### With Profiles

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Start with admin tools
docker-compose --profile tools up -d

# Start everything
docker-compose --profile monitoring --profile tools up -d
```

---

## 🔐 Security Best Practices

### 1. Non-Root User

```dockerfile
# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1001 appuser

# Switch to non-root
USER appuser
```

### 2. Secrets Management

**Development**: Use `.env` file (not committed)

**Production**: Use Docker secrets or external secret managers

```bash
# Create secrets
echo "super_secret_password" | docker secret create postgres_password -

# Use in compose
services:
  postgres:
    secrets:
      - postgres_password
```

### 3. Read-Only Filesystem

```yaml
services:
  api:
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
```

### 4. Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### 5. Security Scanning

```bash
# Scan image for vulnerabilities
docker scan thereview/backend:latest

# Use Trivy
trivy image thereview/backend:latest

# Use Snyk
snyk container test thereview/backend:latest
```

---

## 🏥 Health Checks

### Endpoints

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `/health` | Basic liveness | Docker, Kubernetes |
| `/health/ready` | Dependency check | Kubernetes readiness |
| `/health/live` | Application liveness | Kubernetes liveness |

### Dockerfile Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### Kubernetes Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## 📊 Monitoring & Logging

### View Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow API logs only
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Since timestamp
docker-compose logs --since="2024-01-01T00:00:00" api

# Save logs to file
docker-compose logs api > api.log
```

### Log Rotation

Configured in docker-compose.prod.yml:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service,environment"
```

### Monitoring Stack

```bash
# Start with monitoring
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Access Grafana Alloy UI: http://localhost:12345
# Access OTLP gRPC endpoint: localhost:4317
# Access OTLP HTTP endpoint: localhost:4318
# Access Prometheus-compatible endpoint: http://localhost:9090
# Access Grafana: http://localhost:3000
```

---

## 🚢 Production Deployment

### Pre-Deployment Checklist

- [ ] Set strong secrets (JWT, passwords)
- [ ] Configure database backups
- [ ] Set up SSL/TLS certificates
- [ ] Configure monitoring and alerting
- [ ] Set up log aggregation
- [ ] Test health check endpoints
- [ ] Configure resource limits
- [ ] Enable firewall rules
- [ ] Set up CI/CD pipeline
- [ ] Plan rollback strategy

### Deployment Steps

1. **Build Production Image**
   ```bash
   docker build --target production -t thereview/backend:v1.0.0 .
   docker tag thereview/backend:v1.0.0 thereview/backend:latest
   ```

2. **Push to Registry**
   ```bash
   # Docker Hub
   docker push thereview/backend:v1.0.0
   docker push thereview/backend:latest

   # AWS ECR
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
   docker tag thereview/backend:v1.0.0 <account>.dkr.ecr.us-east-1.amazonaws.com/thereview:v1.0.0
   docker push <account>.dkr.ecr.us-east-1.amazonaws.com/thereview:v1.0.0
   ```

3. **Deploy on Server**
   ```bash
   # Pull latest image
   docker-compose -f docker-compose.prod.yml pull

   # Rolling update with zero downtime
   docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api=4
   docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api=3

   # Verify health
   curl http://localhost:8000/health/ready
   ```

4. **Rollback (if needed)**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build --target production -t thereview/backend:${{ github.sha }} .

      - name: Run tests
        run: |
          docker-compose up -d
          docker-compose exec -T api pytest

      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker push thereview/backend:${{ github.sha }}
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check health status
docker inspect --format='{{json .State.Health}}' thereview-api-prod | jq

# Enter container
docker-compose exec api bash

# Check environment variables
docker-compose exec api env
```

### Database Connection Issues

```bash
# Check if database is healthy
docker-compose ps

# Test connection from API container
docker-compose exec api pg_isready -h postgres -U postgres

# Check MongoDB
docker-compose exec api mongosh mongodb://mongodb:27017/ --eval "db.adminCommand('ping')"

# Check Redis
docker-compose exec api redis-cli -h redis ping
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check specific container
docker stats thereview-api-prod

# Inspect container config
docker inspect thereview-api-prod
```

### Clean Up

```bash
# Remove stopped containers
docker-compose down

# Remove volumes
docker-compose down -v

# Remove unused images
docker image prune -a

# Complete cleanup (DANGER!)
docker system prune -a --volumes
```

---

## 📈 Performance Optimization

### 1. Layer Caching

```dockerfile
# Copy dependency files first (changes less often)
COPY pyproject.toml ./
RUN uv pip install ...

# Copy source code last (changes more often)
COPY app/ ./app/
```

### 2. Multi-Stage Builds

- Builder stage: ~800MB (with build tools)
- Production stage: ~400MB (runtime only)
- **50% size reduction**

### 3. BuildKit

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Parallel builds
docker build --target production .
```

### 4. Build Cache

```bash
# Use inline cache
docker build --cache-from thereview/backend:latest .

# Use registry cache
docker buildx build --cache-from type=registry,ref=thereview/backend:cache .
```

---

## 🌐 Networking

### Bridge Network (Default)

```yaml
networks:
  thereview-network:
    driver: bridge
```

### Custom Network

```yaml
networks:
  thereview-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Service Discovery

```python
# Services can reach each other by name
POSTGRES_HOST=postgres  # Not localhost!
MONGODB_URL=mongodb://mongodb:27017/
REDIS_HOST=redis://redis:6379
```

---

## 💾 Data Persistence

### Named Volumes

```yaml
volumes:
  postgres_data:
    driver: local
    name: thereview-postgres-prod-data
```

### Bind Mounts (Dev Only)

```yaml
volumes:
  - ./app:/app/app:rw  # Hot reload
```

### Backup Volumes

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres thereview_reviews > backup.sql

# Backup MongoDB
docker-compose exec mongodb mongodump --out /backups

# Backup volume
docker run --rm -v thereview-postgres-prod-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data
```

---

## 🎯 Best Practices Summary

✅ **DO:**
- Use multi-stage builds
- Run as non-root user
- Set resource limits
- Use health checks
- Implement log rotation
- Use secrets for sensitive data
- Tag images with versions
- Scan for vulnerabilities
- Document everything

❌ **DON'T:**
- Run as root
- Store secrets in images
- Use `latest` tag in production
- Commit `.env` files
- Skip health checks
- Ignore resource limits
- Use development images in production

---

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [BuildKit](https://docs.docker.com/build/buildkit/)

---

## 🆘 Support

For issues, check:
1. Container logs: `docker-compose logs -f`
2. Health endpoints: `curl http://localhost:8000/health/ready`
3. Resource usage: `docker stats`
4. Network connectivity: `docker network inspect thereview-network`

---

**Your Docker setup is production-ready! 🚀**
