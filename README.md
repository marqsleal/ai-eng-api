# FastAPI with AI Engineering

```
├── Dockerfile
├── Makefile
├── README.md
├── app/
|   ├── api/           # The "View" / Presentation layer (FastAPI routers and endpoints)
|   |   ├── endpoints/
|   |   |   ├── items.py
|   |   |   ├── users.py
|   |   ├── schemas/   # Pydantic models for data validation and serialization
|   ├── core/          # Core configurations and utilities
|   ├── database/      # Database session management
|   ├── models/        # The "Model" layer (SQLAlchemy models)
|   ├── services/      # Business logic (can be considered part of the "Controller" logic)
|   ├── main.py        # Entry point for the application, configures the server and routes
├── pyproject.toml
├── tests/             # Unit and integration tests
```

# Run project 

```bash
make project_init
make db_up
make alembic_upgrade
make obs_up
make run_dev
```

# Recommended Alembic Workflow

Use this flow every time you change SQLAlchemy models.

1. Ensure database is running:

```bash
make db_up
```

2. Apply current pending migrations first (DB must be at head before creating a new revision):

```bash
make alembic_upgrade
```

3. Generate a new migration from model changes:

```bash
make alembic_migrate msg="describe your schema change"
```

4. Review the generated file in `migrations/versions/` and confirm `upgrade()` is not empty.

5. Apply the new migration:

```bash
make alembic_upgrade
```

6. (Optional) Validate Alembic state:

```bash
.venv/bin/python -m alembic current
.venv/bin/python -m alembic heads
```

## Important

- If autogenerate creates an empty migration (`upgrade(): pass`) when models changed, confirm model modules are imported in [`migrations/env.py`](./migrations/env.py) so `Base.metadata` is populated.
