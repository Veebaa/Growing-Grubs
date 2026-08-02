.PHONY: help install format lint type-check test clean setup-dev pre-commit-install

help:
	@echo "Growing Grubs Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup-dev          Setup development environment"
	@echo "  make install            Install dependencies"
	@echo "  make pre-commit-install Install pre-commit hooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format             Format code with Black and isort"
	@echo "  make format-check       Check formatting without modifying"
	@echo "  make lint               Run Flake8 linter"
	@echo "  make type-check         Run mypy type checker"
	@echo "  make test               Run pytest tests"
	@echo "  make test-cov           Run tests with coverage report"
	@echo "  make quality            Run all quality checks (format, lint, type-check)"
	@echo ""
	@echo "Database:"
	@echo "  make migrate            Run database migrations"
	@echo "  make migrate-create     Create a new migration"
	@echo ""
	@echo "Development:"
	@echo "  make run                Run development server"
	@echo "  make clean              Clean cache and build artifacts"
	@echo ""

install:
	pip install -r requirements.txt

setup-dev:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	make pre-commit-install

pre-commit-install:
	pip install pre-commit
	pre-commit install
	pre-commit run --all-files

format:
	black .
	isort .
	@echo "✓ Code formatted successfully"

format-check:
	black --check .
	isort --check-only .
	@echo "✓ Code formatting is valid"

lint:
	flake8
	@echo "✓ Linting passed"

type-check:
	mypy mod/ --ignore-missing-imports
	@echo "✓ Type checking passed"

test:
	python -m pytest tests/ -v --tb=short

test-cov:
	python -m pytest tests/ -v --cov=mod --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

quality: format-check lint type-check
	@echo "✓ All quality checks passed"

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	find . -type d -name '.mypy_cache' -delete
	find . -type d -name 'htmlcov' -delete
	find . -type f -name '.coverage' -delete
	find . -type d -name '.eggs' -delete
	find . -type d -name '*.egg-info' -delete
	@echo "✓ Cache and build artifacts cleaned"

migrate:
	flask db upgrade

migrate-create:
	@read -p "Enter migration message: " msg; \
	flask db migrate -m "$$msg"

run:
	. venv/bin/activate && python server_main.py

.DEFAULT_GOAL := help
