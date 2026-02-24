ifneq (,$(wildcard .env))
include .env
export $(shell sed -n 's/^\([^#][^=]*\)=.*/\1/p' .env)
endif

############################################################################################
# GLOBALS                                                                                  #
############################################################################################

PROJECT_NAME= ai-eng-api
PYTHON_INTERPRETER= python
PYTHON_VER= 3.13

VENV_NAME= .venv
VENV_BIN= $(VENV_NAME)/bin
POETRY = $(VENV_BIN)/python -m poetry

APP_DIR= app
TEST_DIR= tests

API_MODULE = $(APP_DIR).main:app
API_HOST = 0.0.0.0
API_PORT = 8000

############################################################################################
# COMMANDS                                                                                 #
############################################################################################


.PHONY: project_init
project_init: 
	@echo "Creating Python Virtual Environment"
	@$(PYTHON_INTERPRETER)$(PYTHON_VER) -m venv $(VENV_NAME)
	@$(VENV_BIN)/python -m ensurepip --upgrade
	@$(VENV_BIN)/python -m pip install --upgrade pip setuptools wheel
	@echo "Installing Poetry"
	@$(VENV_BIN)/python -m pip install poetry
	@echo "Installing dependencies"
	@$(POETRY) install
	@echo "Virtual Environment Created!"


.PHONY: poetry_reinstall
poetry_reinstall:
	@echo "Installing dependencies"
	@$(POETRY) lock
	@$(POETRY) install


.PHONY: lint
lint:
	@$(VENV_BIN)/python -m ruff check $(APP_DIR) $(TEST_DIR)
	@$(VENV_BIN)/python -m ruff format --check $(APP_DIR) $(TEST_DIR)


.PHONY: format
format:
	@$(VENV_BIN)/python -m ruff check --fix $(APP_DIR) $(TEST_DIR)
	@$(VENV_BIN)/python -m ruff format $(APP_DIR) $(TEST_DIR)


.PHONY: alembic_init
alembic_init:
	@$(VENV_BIN)/python -m alembic init migrations


.PHONY: alembic_migrate
alembic_migrate:
	@$(VENV_BIN)/python -m alembic revision --autogenerate -m "$(msg)"


.PHONY: alembic_upgrade
alembic_upgrade:
	@$(VENV_BIN)/python -m alembic upgrade head


.PHONY: run_dev
run_dev:
	@$(VENV_BIN)/python -m uvicorn $(API_MODULE) \
	--host $(API_HOST) \
	--port $(API_PORT) \
	--reload


.PHONY: run_prd
run_prd:
	@$(VENV_BIN)/python -m uvicorn $(APP_DIR).main:app \
	--host 0.0.0.0 \
	--port 8000 \
	--workers 4


.PHONY: db_up
db_up:
	@docker run -d \
	--name postgres \
	--restart unless-stopped \
	-e POSTGRES_USER="${POSTGRES_USER}" \
	-e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
	-e POSTGRES_DB="${POSTGRES_DB}" \
	-p "${POSTGRES_PORT}:5432" \
	-v postgres_data:/var/lib/postgresql/data \
	--health-cmd="pg_isready -U ${POSTGRES_USER}" \
	--health-interval=10s \
	--health-timeout=5s \
	--health-retries=5 \
	postgres:16


.PHONY: db_down
db_down:
	@docker stop postgres
	@docker rm postgres


.PHONY: obs_up
obs_up:
	@docker run -d --name jaeger \
		-e COLLECTOR_ZIPKIN_HTTP_PORT=9411 \
		-p 16686:16686 \
		-p 4317:4317 \
		-p 4318:4318 \
		jaegertracing/all-in-one:latest
	@echo "Jagger UI: http://localhost:16686"


.PHONY: obs_down
obs_down:
	@docker stop jaeger
	@docker rm jaeger


.PHONY: clean
clean:
	@echo "Cleaning Python cache files..."
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "Cleaning test cache files..."
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "Cleaning build and distribution files..."
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "build" -exec rm -rf {} +
	@find . -type d -name "dist" -exec rm -rf {} +
	@find . -type d -name ".cache" -exec rm -rf {} +
	@echo "Cleaning Jupyter notebook cache..."
	@find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +
	@echo "Clean complete!"
