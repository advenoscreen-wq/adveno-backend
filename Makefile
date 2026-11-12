.PHONY: help install dev up down logs shell test test-unit test-integration test-cov lint format format-check typecheck check migrate migration pre-commit pre-commit-all clean

help:
	@echo "install             Install locked dependencies"
	@echo "dev                 Run API locally"
	@echo "up                  Start Docker Compose services"
	@echo "down                Stop Docker Compose services"
	@echo "logs                Follow service logs"
	@echo "shell               Open an API container shell"
	@echo "test                Run all tests"
	@echo "test-unit           Run unit tests"
	@echo "test-integration    Run integration tests"
	@echo "test-cov            Run tests with coverage"
	@echo "lint                Run Ruff lint"
	@echo "format              Format source and tests"
	@echo "format-check        Check formatting without changes"
	@echo "typecheck           Run Mypy"
	@echo "check               Run all local quality checks"
	@echo "migrate             Apply database migrations"
	@echo "migration           Create an Alembic migration"
	@echo "pre-commit          Run pre-commit on changed files"
	@echo "pre-commit-all      Run pre-commit on all files"
	@echo "clean               Remove local cache artifacts"

install:
	uv sync --all-groups

dev:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec api /bin/sh

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration -m integration

test-cov:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=xml

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy src

check: lint format-check typecheck test

migrate:
	uv run alembic upgrade head

ifndef name
migration:
	@echo "Usage: make migration name=\"description\"" && exit 1
else
migration:
	uv run alembic revision --autogenerate -m "$(name)"
endif

pre-commit:
	uv run pre-commit run

pre-commit-all:
	uv run pre-commit run --all-files

clean:
	uv run python -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov')]"
	uv run python -c "from pathlib import Path; [p.unlink() for p in (Path('.coverage'), Path('coverage.xml')) if p.exists()]"
