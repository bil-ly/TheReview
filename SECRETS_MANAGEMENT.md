# Secrets Management Guide

## Overview

Environment variables in `docker-compose.prod.yml` can come from multiple sources. This guide covers all methods from least to most secure.

---

## 📍 Where Variables Come From

### 1. **`.env` File (Local/Simple Deployments)**

**Best for:** Development, staging, small deployments

```bash
# Step 1: Copy template
cp .env.example .env.prod

# Step 2: Edit with your values
vim .env.prod

# Step 3: Run with env file
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

**Example `.env.prod`:**
```bash
# JWT Settings
JWT_SECRET_KEY=8f7a9b2c1d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a
JWT_ALGORITHM=HS256

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_strong_postgres_password_here
POSTGRES_DB=thereview_reviews

# Gmail
GMAIL_ADDRESS=noreply@thereview.com
APP_PASSWORD=abcd efgh ijkl mnop  # 16-char app password from Google

# MongoDB
MONGO_ROOT_PASSWORD=your_strong_mongo_password_here
```

**⚠️ Security Warning:**
- **NEVER** commit `.env` or `.env.prod` to git
- Add to `.gitignore`
- Use file permissions: `chmod 600 .env.prod`

---

### 2. **Host Environment Variables**

**Best for:** CI/CD pipelines, temporary testing

```bash
# Set environment variables
export JWT_SECRET_KEY="super_secret_key"
export POSTGRES_PASSWORD="strong_password"
export GMAIL_ADDRESS="noreply@thereview.com"
export APP_PASSWORD="gmail_app_password"

# Run docker-compose (it will read from environment)
docker-compose -f docker-compose.prod.yml up -d
```

**In CI/CD (GitHub Actions example):**
```yaml
- name: Deploy
  env:
    JWT_SECRET_KEY: ${{ secrets.JWT_SECRET_KEY }}
    POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
    GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
    APP_PASSWORD: ${{ secrets.APP_PASSWORD }}
  run: |
    docker-compose -f docker-compose.prod.yml up -d
```

---

### 3. **Docker Secrets (Recommended)**

**Best for:** Docker Swarm, production deployments

#### Setup Secrets

```bash
# Generate secrets
./scripts/generate-secrets.sh

# Or create manually
mkdir -p secrets
chmod 700 secrets

# JWT Secret
openssl rand -hex 32 > secrets/jwt_secret_key.txt

# PostgreSQL Password
openssl rand -hex 32 > secrets/postgres_password.txt

# MongoDB Password
openssl rand -hex 32 > secrets/mongo_root_password.txt

# Gmail credentials (manual)
echo "noreply@thereview.com" > secrets/gmail_address.txt
echo "your_gmail_app_password" > secrets/gmail_app_password.txt

# Secure permissions
chmod 600 secrets/*.txt
```

#### Use Secrets

```bash
# Deploy with secrets
docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d
```

**Benefits:**
- ✅ Secrets not in environment (more secure)
- ✅ Encrypted at rest in Docker Swarm
- ✅ Mounted as files in `/run/secrets/`
- ✅ Never appear in logs or `docker inspect`

---

### 4. **External Secret Managers (Production)**

**Best for:** Large-scale production, compliance requirements

#### AWS Secrets Manager

```bash
# Install AWS CLI
pip install awscli

# Store secrets
aws secretsmanager create-secret \
  --name thereview/jwt_secret_key \
  --secret-string "$(openssl rand -hex 32)"

aws secretsmanager create-secret \
  --name thereview/postgres_password \
  --secret-string "$(openssl rand -hex 32)"

# Retrieve in entrypoint script
export JWT_SECRET_KEY=$(aws secretsmanager get-secret-value \
  --secret-id thereview/jwt_secret_key \
  --query SecretString \
  --output text)
```

**Docker Integration:**
```dockerfile
# docker-entrypoint.sh
#!/bin/bash

# Fetch secrets from AWS Secrets Manager
export JWT_SECRET_KEY=$(aws secretsmanager get-secret-value \
  --secret-id thereview/jwt_secret_key --query SecretString --output text)

export POSTGRES_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id thereview/postgres_password --query SecretString --output text)

# Start application
exec "$@"
```

#### HashiCorp Vault

```bash
# Install Vault
brew install vault  # or apt-get install vault

# Initialize Vault
vault server -dev

# Store secrets
vault kv put secret/thereview \
  jwt_secret_key="$(openssl rand -hex 32)" \
  postgres_password="$(openssl rand -hex 32)" \
  gmail_address="noreply@thereview.com" \
  app_password="gmail_app_password"

# Retrieve secrets
vault kv get -field=jwt_secret_key secret/thereview
```

**Docker Integration:**
```bash
# Fetch from Vault in entrypoint
export JWT_SECRET_KEY=$(vault kv get -field=jwt_secret_key secret/thereview)
```

#### Google Cloud Secret Manager

```bash
# Store secret
echo -n "$(openssl rand -hex 32)" | \
  gcloud secrets create jwt_secret_key --data-file=-

# Retrieve secret
gcloud secrets versions access latest --secret="jwt_secret_key"
```

---

## 🔐 Generating Secure Secrets

### JWT Secret Key

```bash
# Method 1: OpenSSL (32 bytes = 256 bits)
openssl rand -hex 32

# Method 2: Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# Example output:
# 8f7a9b2c1d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a
```

### Database Passwords

```bash
# Strong random password
openssl rand -base64 32

# Example output:
# 9xKzJ3mN8vL2qR4wP7tY6uH5gF4dS3aZ1xC0vB9nM8lK
```

### Fernet Key (Encryption)

```bash
# Generate Fernet key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Example output:
# 8f7a9b2c1d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a==
```

### Gmail App Password

**Cannot be generated randomly!** Must create from Google Account:

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Name it "TheReview Backend"
4. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)
5. Use this as `APP_PASSWORD`

---

## 📋 Complete Setup Checklist

### Development

- [ ] Copy `.env.example` to `.env`
- [ ] Set `ENVIRONMENT=development`
- [ ] Use weak passwords (they're local only)
- [ ] Set `DEBUG=true`

```bash
cp .env.example .env
# Edit .env with development values
docker-compose up -d
```

### Production

- [ ] Generate all secrets with `./scripts/generate-secrets.sh`
- [ ] Create `.env.prod` with production values
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Use strong random secrets (32+ characters)
- [ ] Create Gmail app password
- [ ] Set strong database passwords
- [ ] Add `.env.prod` to `.gitignore`
- [ ] Use Docker secrets or external secret manager
- [ ] Test secret retrieval before deployment

```bash
# Option A: .env file
cp .env.example .env.prod
vim .env.prod  # Edit with secrets
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Option B: Docker secrets (recommended)
./scripts/generate-secrets.sh
docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d

# Option C: External secret manager
# Configure AWS Secrets Manager / Vault / GCP Secret Manager
# Update docker-entrypoint.sh to fetch secrets
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🛡️ Security Best Practices

### DO ✅

```bash
# Use strong random secrets
openssl rand -hex 32

# Restrict file permissions
chmod 600 .env.prod
chmod 600 secrets/*.txt

# Use Docker secrets in production
docker-compose -f docker-compose.secrets.yml up -d

# Rotate secrets regularly (every 90 days)
./scripts/rotate-secrets.sh

# Use external secret managers for large deployments
aws secretsmanager create-secret ...

# Store secrets in vault, not code
vault kv put secret/thereview ...
```

### DON'T ❌

```bash
# ❌ Don't commit secrets to git
git add .env.prod  # NEVER!

# ❌ Don't use weak secrets
JWT_SECRET_KEY=password123

# ❌ Don't hardcode secrets in Dockerfile
ENV JWT_SECRET_KEY=hardcoded_secret  # BAD!

# ❌ Don't share .env files via email/Slack
# Use secret sharing tools (1Password, LastPass)

# ❌ Don't use same secrets across environments
# dev, staging, prod should have different secrets

# ❌ Don't log secrets
echo $JWT_SECRET_KEY  # Secrets appear in logs!
```

---

## 🔄 Secret Rotation

### Manual Rotation

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. Update secret file
echo "$NEW_SECRET" > secrets/jwt_secret_key.txt

# 3. Restart services
docker-compose -f docker-compose.prod.yml restart api

# 4. Store old secret for rollback (24-48 hours)
echo "$OLD_SECRET" > secrets/jwt_secret_key.old.txt
```

### Automated Rotation Script

```bash
#!/bin/bash
# scripts/rotate-secrets.sh

# Generate new secrets
NEW_JWT=$(openssl rand -hex 32)
NEW_POSTGRES=$(openssl rand -hex 32)

# Backup old secrets
cp secrets/jwt_secret_key.txt secrets/jwt_secret_key.old.txt
cp secrets/postgres_password.txt secrets/postgres_password.old.txt

# Update secrets
echo "$NEW_JWT" > secrets/jwt_secret_key.txt
echo "$NEW_POSTGRES" > secrets/postgres_password.txt

# Restart services
docker-compose -f docker-compose.prod.yml restart

echo "✓ Secrets rotated successfully"
```

---

## 🆘 Troubleshooting

### Secret Not Found

```bash
# Check if .env file exists
ls -la .env.prod

# Check file permissions
ls -l secrets/

# Verify Docker can read secrets
docker-compose config
```

### Invalid Secret Format

```bash
# Secrets should be single line, no newlines
cat secrets/jwt_secret_key.txt | wc -l  # Should output: 1

# Remove trailing newlines
echo -n "$(cat secrets/jwt_secret_key.txt)" > secrets/jwt_secret_key.txt
```

### Gmail Authentication Failed

```bash
# 1. Verify 2FA is enabled on Gmail
# 2. Generate new app password at https://myaccount.google.com/apppasswords
# 3. Use 16-character password (with spaces removed)
echo "abcdefghijklmnop" > secrets/gmail_app_password.txt
```

---

## 📚 Resources

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [Google Secret Manager](https://cloud.google.com/secret-manager)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)

---

## ✅ Summary

**Development:**
```bash
cp .env.example .env
docker-compose up -d
```

**Production (Simple):**
```bash
cp .env.example .env.prod
vim .env.prod  # Add secrets
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

**Production (Secure):**
```bash
./scripts/generate-secrets.sh
docker-compose -f docker-compose.prod.yml -f docker-compose.secrets.yml up -d
```

**Production (Enterprise):**
```bash
# Use AWS Secrets Manager / Vault
aws secretsmanager create-secret --name thereview/jwt_secret_key ...
# Update docker-entrypoint.sh to fetch secrets
docker-compose -f docker-compose.prod.yml up -d
```

---

**Your secrets are now production-ready! 🔐**
