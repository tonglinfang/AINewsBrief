.PHONY: help install test format lint clean run setup-test

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make install-dev  - Install with dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Run ruff linter"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make run          - Run the AI News Brief workflow"
	@echo "  make setup-test   - Test environment setup"

install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

format:
	black src/ tests/ scripts/

lint:
	ruff check src/ tests/ scripts/

lint-fix:
	ruff check --fix src/ tests/ scripts/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/

run:
	python -m src.agent

setup-test:
	python scripts/test_setup.py

# GitHub Actions local testing (requires act: https://github.com/nektos/act)
act-test:
	act -j generate-brief --secret-file .env
