# Requirements Files

The `requirements-*.txt` files are kept for reference and backward compatibility,
but the project now uses **uv** with `pyproject.toml` for dependency management.

## For New Users

Use `uv` for dependency management:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync project dependencies (creates .venv automatically)
uv sync --all-extras

# Run commands with uv run
uv run python server/server.py
uv run pytest
```

## Why uv?

- **Faster**: 10-100x faster than pip
- **Modern**: Built in Rust, designed for Python 3.12+
- **Compatible**: Works with existing `pyproject.toml` standards
- **Reliable**: Deterministic dependency resolution

## Dependencies

All dependencies are now defined in `pyproject.toml`:

- **Base**: numpy (required by both client and server)
- **Server**: flask, werkzeug
- **Client**: requests
- **Dev**: pytest, pytest-cov, ruff, pre-commit

## Updating Dependencies

To update a dependency:

1. Edit `pyproject.toml`
2. Run `uv sync --all-extras`
3. Test the changes with `uv run pytest`
4. Commit `pyproject.toml` and `uv.lock` (if changed)
