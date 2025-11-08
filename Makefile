.PHONY: help install test lint format coverage clean docker-build docker-up docker-down server client pre-commit

help:
	@echo "CodonSoup - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install all dependencies with uv"
	@echo "  make install-dev   - Install dev dependencies"
	@echo "  make pre-commit    - Install pre-commit hooks"
	@echo ""
	@echo "Running:"
	@echo "  make server        - Start server"
	@echo "  make client        - Start client"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make coverage      - Run tests with coverage report"
	@echo "  make lint          - Run ruff linter"
	@echo "  make format        - Format code with ruff"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Remove temporary files"

install:
	uv sync --extra server --extra client

install-dev:
	uv sync --all-extras

pre-commit:
	uv run pre-commit install

test:
	uv run pytest

coverage:
	uv run pytest --cov=client --cov=server --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .ruff_cache
	rm -rf dist
	rm -rf build
	rm -rf .venv

server:
	uv run python server/server.py

client:
	uv run python client/client.py --server=http://localhost:8080

docker-build:
	docker-compose build

docker-up:
	docker-compose up

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-scale:
	docker-compose up --scale client=10
