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