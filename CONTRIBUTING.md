# Contributing to CodonSoup

Thank you for your interest in contributing to CodonSoup! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/CodonSoup.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit your changes: `git commit -m "Description of changes"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone your fork
git clone https://github.com/YOUR_USERNAME/CodonSoup.git
cd CodonSoup

# Sync all dependencies with uv (creates .venv automatically)
uv sync --all-extras

# Set up pre-commit hooks (recommended)
make pre-commit
# or: uv run pre-commit install
```

## Code Style

The project uses **Ruff** for linting and formatting:

- Follow PEP 8 style guidelines (enforced by Ruff)
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and concise
- Add type hints where appropriate

**Before committing:**
```bash
# Auto-format code
make format

# Check for issues
make lint
```

Pre-commit hooks will automatically run these checks.

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting PR
- Aim for high test coverage (>80%)
- Include both unit tests and integration tests

```bash
# Run all tests
make test
# or: uv run pytest

# Run with coverage report
make coverage
# This generates htmlcov/index.html

# Run specific test file
uv run pytest tests/client/test_organism.py -v
```

## Pull Request Guidelines

- **Title**: Clear, concise description of the change
- **Description**: Explain what and why, not just how
- **Tests**: Include tests for new functionality
- **Documentation**: Update README.md if needed
- **Small PRs**: Keep changes focused and manageable

## Areas for Contribution

### High Priority
- Performance optimizations
- Additional mutation operators
- New phenotype traits
- Visualization improvements
- Documentation enhancements

### Medium Priority
- Additional tests
- Code refactoring
- Docker improvements
- API extensions

### Ideas for Features
- Sexual reproduction (genome crossover)
- Predator-prey dynamics
- Multiple environmental zones
- Genome visualization
- Phylogenetic tree tracking
- Real-time 2D rendering of organisms

## Reporting Bugs

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Minimal steps to reproduce the issue
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, etc.
6. **Logs/Screenshots**: Any relevant output

## Feature Requests

Feature requests are welcome! Please:

1. Check if the feature already exists
2. Explain the use case
3. Describe the proposed solution
4. Consider implementation complexity

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Give credit where due
- Maintain professional communication

## Questions?

Feel free to:
- Open an issue for questions
- Join discussions in existing issues
- Reach out to maintainers

Thank you for contributing to CodonSoup!
