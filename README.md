# ai-eng-api

## Project Structure

```text
.
├── Dockerfile              # API container image
├── Makefile                # local developer workflow commands
├── README.md               # project documentation
├── docker-compose.yml      # local stack: api, postgres, jaeger, ollama
├── alembic.ini             # Alembic configuration
├── app/
│   ├── main.py             # FastAPI app factory and router registration
│   ├── api/                # HTTP layer
│   │   ├── endpoints/      # route handlers (users, model-versions, conversations, health)
│   │   └── schemas/        # Pydantic request/response schemas
│   ├── core/               # settings, logging, observability utilities
│   ├── database/           # async SQLAlchemy engine/session and DB dependencies
│   ├── models/             # SQLAlchemy ORM models
│   ├── repositories/       # data access layer (queries and persistence)
│   └── services/           # business services
│       └── llm/            # LLM integration (typed contracts, Ollama client, service)
├── migrations/             # Alembic migration environment and versions
├── docs/                   # API docs and route examples
└── tests/                  # unit/integration-style tests
```

Async FastAPI backend for AI workflows with:
- user, model-version, and conversation management
- local LLM generation via Ollama
- PostgreSQL + Alembic migrations
- optional Jaeger/OpenTelemetry stack

## Main Features

- Async SQLAlchemy session and async endpoints
- CRUD for:
  - `/users`
  - `/model-versions`
  - `/conversations`
- LLM integration on existing endpoint:
  - `POST /conversations` with `response` omitted triggers Ollama generation
- Structured logging (JSON/HUMAN)

## Prerequisites

- Python 3.13
- Docker + Docker Compose

## Quick Start (Local Dev)

1. Create virtualenv and install dependencies:

```bash
make project_init
```

2. Start dependencies:

```bash
make db_up
make llm_up
make obs_up
```

3. Run migrations:

```bash
make alembic_upgrade
```

4. Run API:

```bash
make run_dev
```

API: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`
OpenAPI JSON: `http://localhost:8000/openapi.json`

## Local LLM (Ollama)

- Compose service: `ollama`
- Default model is read from `.env`:
  - `OLLAMA_DEFAULT_MODEL=llama3.2:3b`
- `make llm_up`:
  - starts Ollama
  - waits until ready
  - pulls `$(OLLAMA_DEFAULT_MODEL)`

Check models:

```bash
docker compose exec ollama ollama list
```

## API Usage References

- Full route examples: [docs/routes.md](./docs/routes.md)

Quick setup requests:

```bash
# create test user
curl -s -X POST http://localhost:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"email":"test-user@example.com"}'

# register default local model in model_version
curl -s -X POST http://localhost:8000/model-versions \
  -H 'Content-Type: application/json' \
  -d '{"provider":"ollama","model_name":"llama3.2:3b","version_tag":"v1"}'
```

## Migrations

Typical workflow after model changes:

```bash
make db_up
make alembic_upgrade
make alembic_migrate msg="describe change"
make alembic_upgrade
```

Optional checks:

```bash
.venv/bin/python -m alembic current
.venv/bin/python -m alembic heads
```

## Quality Checks

```bash
make lint
make run_test
```

## Common Make Targets

- `project_init`: bootstrap local environment
- `run_dev`: start uvicorn with reload
- `db_up` / `db_down`: PostgreSQL
- `llm_up` / `llm_down`: Ollama
- `obs_up` / `obs_down`: Jaeger
- `alembic_upgrade`: apply migrations
- `alembic_migrate msg="..."`: generate migration

## Environment Variables

Core variables are in `.env.example`.

Important LLM/database vars:
- `POSTGRES_HOSTNAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`
- `OLLAMA_BASE_URL`
- `OLLAMA_DEFAULT_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `OLLAMA_STARTUP_CHECK_ENABLED`
- `OPENAPI_ENABLED`, `OPENAPI_JSON_PATH`
- `SWAGGER_UI_ENABLED`, `SWAGGER_UI_PATH`
