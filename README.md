# Adveno Backend

Initial development foundation for the Adveno backend MVP. This repository
currently contains infrastructure and application bootstrap only; business
features, API resources, use cases, and database entities are intentionally
not implemented.

## Prerequisites

- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/)
- Docker and Docker Compose
- Make (optional convenience wrapper)

## Local setup

```bash
uv sync --all-groups
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn main:app --reload
```

The API is available at `http://localhost:8000`. Interactive OpenAPI
documentation is available at `/docs`.

## Docker setup

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f
docker compose down
```

Compose starts PostgreSQL, waits for its health check, applies Alembic
migrations, and starts the API. PostgreSQL data is stored in the named
`postgres_data` volume.

## Development commands

Run `make help` to list all supported commands. Common checks are:

```bash
make test
make lint
make format-check
make typecheck
make pre-commit-all
```

Install hooks with `uv run pre-commit install`.

## Architecture

Production code lives directly under `src/` and follows Clean Architecture:
`drivers`, `domain`, `application`, `adapters`, `bootstrap`, and `config`.
Unit and integration tests mirror the source package structure under
`tests/unit` and `tests/integration`.

## Configuration

Copy `.env.example` to `.env` for local settings. Never commit `.env` or
real credentials. Production configuration must provide a non-placeholder
`JWT_SECRET` and a managed database URL.
