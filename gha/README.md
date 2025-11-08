# GitHub Actions Workflows

This directory contains GitHub Actions workflow files that can be moved to `.github/workflows/` when ready.

## Installation

To enable these workflows:

```bash
# Create the workflows directory if it doesn't exist
mkdir -p .github/workflows

# Copy all workflow files
cp gha/*.yml .github/workflows/

# Commit and push
git add .github/workflows/
git commit -m "Add GitHub Actions workflows"
git push
```

## Available Workflows

### 1. tests.yml - Automated Testing

**Triggers:** Push to main/develop/claude/* branches, PRs to main/develop

**What it does:**
- Tests on Python 3.9, 3.10, 3.11, 3.12
- Installs dependencies with `uv sync --all-extras`
- Runs ruff linter and formatter checks
- Runs pytest with coverage
- Uploads coverage to Codecov (requires CODECOV_TOKEN secret)
- Archives HTML coverage reports as artifacts

**Requirements:**
- None (works out of the box)
- Optional: Add `CODECOV_TOKEN` secret for coverage uploads

### 2. docker.yml - Docker Image Builds

**Triggers:** Push to main, tags (v*), PRs to main

**What it does:**
- Builds server Docker image
- Builds client Docker image
- Tests docker-compose setup
- Pushes images to GitHub Container Registry (on main branch)
- Creates multi-platform builds with caching

**Requirements:**
- Automatic (uses GITHUB_TOKEN)
- Images pushed to `ghcr.io/OWNER/REPO-server` and `ghcr.io/OWNER/REPO-client`

### 3. lint.yml - Code Quality Checks

**Triggers:** Push to main/develop/claude/* branches, PRs to main/develop

**What it does:**
- **Lint job**: Runs ruff linter and formatter checks
- **Security job**: Runs safety check for known vulnerabilities (optional, continues on error)
- **Complexity job**: Checks for complex code (optional, continues on error)
- All jobs use uv for dependency management

**Requirements:**
- None (works out of the box)

## Workflow Features

### Using uv

All workflows use the official `astral-sh/setup-uv@v3` action:

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v3
  with:
    version: "latest"

- name: Set up Python
  run: uv python install 3.11

- name: Install dependencies
  run: uv sync --all-extras
```

### Matrix Testing

The tests workflow runs on multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11', '3.12']
```

### Artifacts

Coverage reports are saved as artifacts for 7 days:

```yaml
- name: Archive coverage report
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report-${{ matrix.python-version }}
    path: htmlcov/
    retention-days: 7
```

### Caching

Docker builds use GitHub Actions cache for faster builds:

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

## Badge Examples

Add these to your README.md:

```markdown
[![Tests](https://github.com/OWNER/REPO/workflows/Tests/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/tests.yml)
[![Docker Build](https://github.com/OWNER/REPO/workflows/Docker%20Build/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/docker.yml)
[![Code Quality](https://github.com/OWNER/REPO/workflows/Code%20Quality/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/OWNER/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/OWNER/REPO)
```

Replace `OWNER/REPO` with your GitHub username and repository name.

## Optional: Codecov Setup

To enable coverage uploads:

1. Sign up at https://codecov.io
2. Add your repository
3. Get your upload token
4. Add as repository secret:
   - Go to Settings → Secrets and variables → Actions
   - Add new secret: `CODECOV_TOKEN` = your token

## Customization

### Change Test Python Versions

Edit `tests.yml`:

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']  # Only test on latest versions
```

### Change Docker Registry

Edit `docker.yml`:

```yaml
env:
  REGISTRY: docker.io  # Use Docker Hub instead
  IMAGE_NAME: username/codonsoup
```

### Disable Optional Checks

In `lint.yml`, remove or comment out the `security` and `complexity` jobs if not needed.

## Troubleshooting

### Tests fail on CI but pass locally

- Ensure `.venv` is in `.gitignore`
- Check that `uv.lock` is committed
- Verify all test dependencies are in `pyproject.toml`

### Docker build fails

- Check that `pyproject.toml` is at repository root
- Verify `Dockerfile.server` and `Dockerfile.client` exist
- Ensure `uv sync` commands in Dockerfiles are correct

### uv not found

- Workflow should use `astral-sh/setup-uv@v3` action
- If using self-hosted runners, install uv manually

## Manual Workflow Dispatch

You can add manual triggers to any workflow:

```yaml
on:
  push:
    branches: [ main ]
  workflow_dispatch:  # Add this for manual runs
```

Then run from GitHub UI: Actions → Select workflow → Run workflow

## Status Checks

To require workflows before merging:

1. Go to Settings → Branches
2. Add branch protection rule for `main`
3. Enable "Require status checks to pass before merging"
4. Select workflows: `test`, `lint`, etc.
