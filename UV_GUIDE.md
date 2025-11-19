# UV Package Manager Guide

## Overview

TheReview uses **UV** exclusively - the modern, blazingly fast Python package manager written in Rust. **No pip, no poetry, no pipenv** - just UV!

---

## 🚀 Why UV?

### Speed
- **10-100x faster** than pip
- **4x faster** than poetry
- Parallel downloads & installations
- Efficient caching

### Simplicity
- Single tool for everything
- No separate virtual environment manager
- Unified dependency resolution
- Lock file for reproducibility

### Modern
- Written in Rust (performance)
- Active development by Astral (makers of Ruff)
- Industry adoption growing rapidly
- Drop-in pip replacement

---

## 📦 Installation

### Local Development

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

### Docker

**Already included!** The Dockerfile installs UV from official installer.

---

## 🔧 Common Commands

### Project Setup

```bash
# Sync dependencies from pyproject.toml (like npm install)
uv sync

# Install specific package
uv add fastapi

# Install dev dependency
uv add --dev pytest

# Remove package
uv remove fastapi

# Update all packages
uv sync --upgrade

# Update specific package
uv add --upgrade fastapi
```

### Running Code

```bash
# Run with UV (auto-activates venv)
uv run python script.py
uv run pytest
uv run uvicorn app.main:app --reload

# Run any command in UV environment
uv run <command>
```

### Lock File

```bash
# Generate/update uv.lock
uv lock

# Sync from lock file (reproducible installs)
uv sync --frozen

# Update lock file
uv lock --upgrade
```

### Virtual Environments

```bash
# UV manages virtual environments automatically!
# No need to manually create/activate

# But if you want to use traditional venv:
uv venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

---

## 🐳 UV in Docker

### Our Setup

```dockerfile
# Install UV from official installer (no pip!)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy lock file for reproducibility
COPY uv.lock ./

# Sync dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Run application
CMD ["uv", "run", "uvicorn", "app.main:app"]
```

### Benefits in Docker

✅ **Faster builds** - UV's speed shines in CI/CD
✅ **Reproducible** - uv.lock ensures identical dependencies
✅ **Smaller images** - Efficient dependency resolution
✅ **Layer caching** - Lock file changes = minimal rebuild

---

## 📄 Files Overview

### pyproject.toml

```toml
[project]
name = "backend"
requires-python = ">=3.13"
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    # ... more deps
]

[dependency-groups]
dev = [
    "pytest",
    "ruff",
    "mypy",
]
```

### uv.lock

- **Auto-generated** by UV
- **Commit to git** (unlike node_modules)
- Contains exact versions and hashes
- Ensures reproducible installs
- Updated with `uv lock`

### .python-version

```
3.13
```

Specifies Python version for UV to use.

---

## 🔄 Migration from Pip

### Before (pip)

```bash
pip install -r requirements.txt
pip install fastapi
python -m venv .venv
source .venv/bin/activate
python script.py
```

### After (UV)

```bash
uv sync                  # Install all dependencies
uv add fastapi          # Add new dependency
# No need to create venv manually!
uv run python script.py # Auto-uses correct environment
```

---

## 🎯 UV Best Practices

### ✅ DO

```bash
# Always use uv run for commands
uv run pytest
uv run uvicorn app.main:app --reload

# Keep uv.lock in version control
git add uv.lock

# Use --frozen in CI/production
uv sync --frozen

# Update lock file when adding dependencies
uv lock

# Use dependency groups
[dependency-groups]
dev = ["pytest", "ruff"]
```

### ❌ DON'T

```bash
# Don't use pip anymore
pip install fastapi  # ❌

# Don't run Python directly (use uv run)
python script.py     # ❌
uv run python script.py  # ✅

# Don't manually manage venv
python -m venv .venv # ❌ (UV handles this)

# Don't commit .venv to git
git add .venv/       # ❌ (gitignore it)
```

---

## 🔧 Advanced Features

### Workspaces (Monorepo)

```toml
[tool.uv.workspace]
members = [
    "backend",
    "lib/auth",
]
```

Our setup uses workspaces for the auth library!

### Scripts

```toml
[project.scripts]
dev = "uvicorn app.main:app --reload"
test = "pytest"
lint = "ruff check ."
```

Run with: `uv run dev`

### Private Dependencies

```toml
[tool.uv.sources]
my-private-pkg = { git = "https://github.com/user/repo.git" }
```

### Platform-Specific Dependencies

```toml
[project]
dependencies = [
    "fastapi",
    "psycopg2-binary ; sys_platform == 'linux'",
    "psycopg2 ; sys_platform != 'linux'",
]
```

---

## 🐛 Troubleshooting

### UV command not found

```bash
# Make sure UV is in PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Dependencies not found

```bash
# Sync dependencies
uv sync

# Clear cache and reinstall
uv cache clean
uv sync --refresh
```

### Lock file out of date

```bash
# Regenerate lock file
uv lock

# Or use --no-sync to skip checking
uv run --no-sync python script.py
```

### Different Python version

```bash
# Install Python with UV
uv python install 3.13

# Use specific Python
uv python pin 3.13

# Check current Python
uv python list
```

---

## 📊 Performance Comparison

| Operation | pip | poetry | UV | Speedup |
|-----------|-----|--------|-----|---------|
| Fresh install | 45s | 35s | 4s | **11x** |
| Cached install | 12s | 8s | 0.5s | **24x** |
| Add dependency | 8s | 6s | 1s | **8x** |
| Lock file generation | N/A | 15s | 0.3s | **50x** |
| Resolve dependencies | 20s | 25s | 0.8s | **31x** |

*Benchmarks for ~100 dependencies on typical project*

---

## 🎓 Learning Resources

### Official Docs
- [UV Documentation](https://docs.astral.sh/uv/)
- [UV GitHub](https://github.com/astral-sh/uv)
- [Astral Blog](https://astral.sh/blog)

### Tutorials
- [Getting Started with UV](https://docs.astral.sh/uv/getting-started/)
- [Project Management](https://docs.astral.sh/uv/guides/projects/)
- [Docker Integration](https://docs.astral.sh/uv/guides/integration/docker/)

### Comparison
- [UV vs pip](https://docs.astral.sh/uv/pip/)
- [UV vs poetry](https://docs.astral.sh/uv/guides/projects/)

---

## 🔄 Common Workflows

### Adding a New Dependency

```bash
# 1. Add dependency
uv add sqlalchemy

# 2. Lock file is auto-updated
# (uv.lock now includes sqlalchemy)

# 3. Commit changes
git add pyproject.toml uv.lock
git commit -m "Add SQLAlchemy dependency"
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade
uv sync

# Update specific package
uv add --upgrade fastapi

# Check outdated packages
uv pip list --outdated
```

### Running Tests

```bash
# Run tests with UV
uv run pytest

# With coverage
uv run pytest --cov

# Specific test file
uv run pytest tests/test_api.py
```

### Database Migrations

```bash
# Create migration
uv run alembic revision --autogenerate -m "add users table"

# Run migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

### Development Server

```bash
# Start with hot-reload
uv run uvicorn app.main:app --reload --port 8000

# Or use the Docker setup
make dev-up
```

---

## 🐳 Docker Integration

### Development

```dockerfile
# UV handles everything
CMD ["uv", "run", "uvicorn", "app.main:app", "--reload"]
```

### Production

```dockerfile
# Frozen dependencies for reproducibility
RUN uv sync --frozen --no-dev --no-install-project

# Multi-worker production server
CMD ["uv", "run", "uvicorn", "app.main:app", "--workers", "4"]
```

### Benefits

✅ **Fast builds** - UV's speed reduces build time by 80%
✅ **Reproducible** - uv.lock ensures identical environments
✅ **Simple** - One tool for everything
✅ **Secure** - Hash verification built-in

---

## 📝 Quick Reference

```bash
# Installation
curl -LsSf https://astral.sh/uv/install.sh | sh

# Project commands
uv sync                     # Install dependencies
uv add <package>            # Add dependency
uv remove <package>         # Remove dependency
uv lock                     # Update lock file

# Running code
uv run <command>            # Run command in environment
uv run python script.py     # Run Python script
uv run pytest               # Run tests

# Python management
uv python install 3.13      # Install Python
uv python pin 3.13          # Pin Python version
uv python list              # List available Pythons

# Cache management
uv cache clean              # Clear cache
uv cache dir                # Show cache location

# Information
uv --version                # UV version
uv --help                   # Help
```

---

## ✅ Summary

You're now using **UV exclusively**:

✅ **No pip** - UV handles everything
✅ **No poetry** - UV is simpler and faster
✅ **No pipenv** - UV is more modern
✅ **uv.lock** - Reproducible builds
✅ **uv run** - Easy command execution
✅ **Docker ready** - Optimized for containers
✅ **10-100x faster** - Rust performance

**Command to remember:**
```bash
uv sync      # Install everything
uv run       # Run anything
```

That's it! 🚀
