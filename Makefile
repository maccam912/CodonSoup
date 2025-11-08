.PHONY: help install test lint clean docker-build docker-up docker-down server client

help:
	@echo "CodonSoup - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install all dependencies"
	@echo "  make install-dev   - Install dev dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make server        - Start server"
	@echo "  make client        - Start client"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters"
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
	pip install -r requirements-server.txt
	pip install -r requirements-client.txt

install-dev:
	pip install -r requirements-server.txt
	pip install -r requirements-client.txt
	pip install -r requirements-test.txt
	pip install black flake8 isort

test:
	pytest

test-cov:
	pytest --cov=client --cov=server --cov-report=html --cov-report=term

lint:
	black --check server/ client/ tests/
	isort --check-only server/ client/ tests/
	flake8 server/ client/ tests/ --max-line-length=127

format:
	black server/ client/ tests/
	isort server/ client/ tests/

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build

server:
	cd server && python server.py

client:
	cd client && python client.py --server=http://localhost:8080

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
