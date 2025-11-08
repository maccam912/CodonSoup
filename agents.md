# CodonSoup AI Agent Configuration

This document provides guidance for AI agents working with the CodonSoup project.

## Project Overview

CodonSoup is a distributed artificial life simulation featuring:
- **Emergent gene regulatory networks** from variable-length genomes
- **Client-server architecture** for distributed evolution
- **Gene expression system** with START/STOP codons, overlapping genes, and junk DNA
- **Modern Python tooling** with uv, ruff, and pre-commit

## Package Manager: uv

**CRITICAL**: This project uses `uv` as the package manager. Always use `uv` commands, never bare `python` or `pip`.

### Correct Commands

```bash
# Install/sync dependencies
uv sync

# Run Python scripts
uv run python server/server.py
uv run python client/client.py

# Run pytest
uv run pytest

# Run ruff
uv run ruff check .
uv run ruff format .

# Run pre-commit
uv run pre-commit run --all-files
```

### Incorrect Commands (DO NOT USE)

```bash
# ❌ WRONG
python server/server.py
pip install -e .
pytest

# ✅ CORRECT
uv run python server/server.py
uv sync
uv run pytest
```

## Project Structure

```
CodonSoup/
├── server/
│   ├── server.py              # Flask API server
│   └── templates/
│       └── dashboard.html     # Web dashboard
├── client/
│   ├── organism.py            # Gene expression & evolution
│   ├── world.py               # Simulation environment
│   └── client.py              # Client runner
├── tests/
│   ├── client/                # Client tests
│   └── server/                # Server tests
├── pyproject.toml             # Project config & dependencies
├── .pre-commit-config.yaml    # Pre-commit hooks
└── Makefile                   # Convenience commands
```

## Key Files

### pyproject.toml
- Main project configuration
- Dependencies defined in `[project.dependencies]` and `[project.optional-dependencies]`
- Tool configurations for pytest, ruff, and coverage

### server/server.py
- Flask API with endpoints: `/api/genome` (GET/POST), `/api/gene_stats`, `/api/pool_status`
- SQLite database for genome pool management
- Web dashboard at root `/`

### client/organism.py
- `extract_genes()`: Extracts genes from genomes using START/STOP codons
- `interpret_gene()`: Converts genes to protein effects
- `Organism` class: Handles gene expression, movement, metabolism, reproduction

### client/world.py
- `World` class: 120×120 simulation environment
- Light gradient and nutrient field
- Population dynamics

## Development Workflow

### 1. Initial Setup
```bash
# Sync dependencies (creates .venv automatically)
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### 2. Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=client --cov=server --cov-report=html

# Run specific test
uv run pytest tests/client/test_organism.py -v
```

### 3. Code Quality
```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### 4. Running the System
```bash
# Terminal 1: Start server
uv run python server/server.py

# Terminal 2: Run client
uv run python client/client.py --server=http://localhost:8080
```

## Common Tasks

### Adding a New Dependency
1. Edit `pyproject.toml`
2. Add to appropriate section: `[project.dependencies]`, `[project.optional-dependencies.server]`, etc.
3. Run `uv sync`

### Running a Single Test File
```bash
uv run pytest tests/client/test_organism.py -v
```

### Checking Coverage
```bash
uv run pytest --cov=client --cov=server --cov-report=term-missing
# HTML report: htmlcov/index.html
```

### Debugging
```bash
# Run with verbose output
uv run python client/client.py --server=http://localhost:8080 --generations=5

# Run in offline mode (no server)
uv run python client/client.py --offline --generations=10
```

## Testing Guidelines

### Test Organization
- `tests/client/test_organism.py`: Tests for gene expression, organism behavior
- `tests/client/test_world.py`: Tests for simulation environment
- `tests/server/test_server.py`: Tests for API endpoints

### Running Specific Test Classes
```bash
uv run pytest tests/client/test_organism.py::TestGeneExtraction -v
```

### Test Coverage Requirements
- No strict threshold (informational only)
- Coverage reports show missing lines
- HTML report provides detailed line-by-line coverage

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

1. **File checks**: Trailing whitespace, EOF fixer, YAML/JSON/TOML validation
2. **Ruff format**: Auto-formats code
3. **Ruff lint**: Checks for issues
4. **Pytest**: Runs full test suite with coverage

To run manually:
```bash
uv run pre-commit run --all-files
```

## Docker Usage

Docker containers also use uv:

```bash
# Build images
docker-compose build

# Start server + 3 clients
docker-compose up

# Scale clients
docker-compose up --scale client=10
```

## API Endpoints

### GET /api/genome
Returns a high-fitness genome from the pool.

### POST /api/genome
Submit a genome to the pool.
```json
{
  "genome": [0.5, 0.96, ...],
  "fitness": 42.5,
  "client_id": "client_123"
}
```

### GET /api/gene_stats
Returns gene length distribution and fitness statistics.

### GET /api/pool_status
Returns overall pool statistics (total genomes, avg fitness, etc.).

### GET /health
Health check endpoint.

## Debugging Common Issues

### Import Errors
```bash
# Ensure dependencies are synced
uv sync

# Check Python path
uv run python -c "import sys; print(sys.path)"
```

### Test Failures
```bash
# Run with verbose output
uv run pytest -v --tb=long

# Run single test for debugging
uv run pytest tests/client/test_organism.py::TestGeneExtraction::test_simple_gene -v
```

### Server Won't Start
```bash
# Check port 8080 is free
lsof -i :8080

# Run server with debug output
uv run python server/server.py
```

## Gene Expression System

### Genome Structure
- List of floats [0, 1]
- Variable length (typically 50-200 codons)
- Circular topology

### Gene Detection
- **START**: value > 0.95
- **STOP**: value < 0.05
- **Valid gene**: 3-20 codons between START and STOP

### Protein Properties
- **Trait**: Determined by gene content hash (mod 4)
  - 0: Speed (0-3)
  - 1: Turn rate (0-0.5)
  - 2: Phototaxis (-1 to +1)
  - 3: Efficiency (0-1)
- **Magnitude**: Mean of gene values, normalized to [-1, 1]
- **Regulatory**: True if gene contains extreme values (<0.1 or >0.9)

### Mutations
- **Point mutation**: 2% per codon
- **Insertion**: 0.5% per codon
- **Deletion**: 0.3% per codon
- **Duplication**: 1% per reproduction (copies segment of 5-15 codons)

## Performance Tips

- Use `--quiet` flag for clients to reduce output
- Run server on one machine, clients on multiple machines for distributed evolution
- Use Docker for easy deployment
- Monitor dashboard at `http://localhost:8080` for real-time statistics

## Contributing

When making changes:
1. Create a feature branch
2. Make changes
3. Run `uv run pytest` to ensure tests pass
4. Run `uv run ruff format .` to format code
5. Run `uv run ruff check .` to check for issues
6. Commit (pre-commit hooks will run automatically)
7. Push and create PR

## Environment Variables

Create `.env` file (based on `.env.example`):
```bash
SERVER_PORT=8080
SERVER_HOST=0.0.0.0
CLIENT_SERVER_URL=http://localhost:8080
DB_PATH=data/soup.db
```

## Useful Commands Reference

```bash
# Setup
uv sync                          # Install dependencies
uv run pre-commit install        # Setup pre-commit hooks

# Development
uv run python server/server.py   # Start server
uv run python client/client.py   # Run client
uv run pytest                    # Run tests
uv run pytest --cov=client --cov=server  # Tests with coverage
uv run ruff check .              # Lint
uv run ruff format .             # Format
uv run pre-commit run --all-files  # Run all pre-commit hooks

# Docker
docker-compose up                # Start services
docker-compose up --scale client=10  # Scale clients
docker-compose logs -f           # View logs
docker-compose down              # Stop services
```

## Notes for AI Agents

- **Always use `uv run`** for Python commands
- **Always use `uv sync`** for dependency management
- Pre-commit hooks will automatically format and check code
- Tests must pass before committing
- Code coverage is tracked but no strict threshold enforced
- Project uses modern Python tooling (uv, ruff, pytest)
- All commands should work from project root directory
