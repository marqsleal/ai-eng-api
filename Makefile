-include .env

SHELL := /bin/bash

############################################################################################
# GLOBALS                                                                                  #
############################################################################################

PYTHON_INTERPRETER = python
PYTHON_VER = 3.13
PYTHON = $(PYTHON_INTERPRETER)$(PYTHON_VER)
COMPOSE = docker compose

VENV_NAME = .venv
VENV_BIN = $(VENV_NAME)/bin
VENV_PYTHON = $(VENV_BIN)/python
POETRY = $(VENV_PYTHON) -m poetry

APP_DIR = app
TEST_DIR = tests

API_MODULE = $(APP_DIR).main:app
API_HOST = 0.0.0.0
API_PORT = 8000
API_WORKERS = 4

############################################################################################
# COMMANDS                                                                                 #
############################################################################################

## setup
.PHONY: project_init
project_init:
	@echo "Creating Python Virtual Environment"
	@$(PYTHON) -m venv $(VENV_NAME)
	@$(VENV_PYTHON) -m ensurepip --upgrade
	@$(VENV_PYTHON) -m pip install --upgrade pip setuptools wheel
	@echo "Installing Poetry"
	@$(VENV_PYTHON) -m pip install poetry
	@echo "Installing dependencies"
	@$(POETRY) install
	@echo "Virtual Environment Created!"


.PHONY: poetry_reinstall
poetry_reinstall:
	@echo "Installing dependencies"
	@$(POETRY) lock
	@$(POETRY) install


## migrations
.PHONY: alembic_init
alembic_init:
	@$(VENV_PYTHON) -m alembic init migrations


.PHONY: alembic_upgrade
alembic_upgrade:
	@$(VENV_PYTHON) -m alembic upgrade head


.PHONY: alembic_migrate
alembic_migrate:
	@$(VENV_PYTHON) -m alembic revision --autogenerate -m "$(msg)"


## tests
.PHONY: test
test:
	@$(VENV_PYTHON) -m pytest $(TEST_DIR)


## lint/format
.PHONY: lint
lint:
	@$(VENV_PYTHON) -m ruff check $(APP_DIR) $(TEST_DIR)
	@$(VENV_PYTHON) -m ruff format --check $(APP_DIR) $(TEST_DIR)


.PHONY: format
format:
	@$(VENV_PYTHON) -m ruff check --fix $(APP_DIR) $(TEST_DIR)
	@$(VENV_PYTHON) -m ruff format $(APP_DIR) $(TEST_DIR)


## run
.PHONY: run_dev
run_dev: stack_up


.PHONY: run_prd
run_prd:
	@$(VENV_PYTHON) -m uvicorn $(API_MODULE) \
		--host $(API_HOST) \
		--port $(API_PORT) \
		--workers $(API_WORKERS)


## docker helpers
.PHONY: api_up
api_up:
	@$(COMPOSE) up --build --detach api
	@echo "API running via docker compose; use `make logs_api` to follow logs."


.PHONY: api_stop
api_stop:
	@$(COMPOSE) stop api


.PHONY: api_restart
api_restart:
	@$(COMPOSE) restart api


.PHONY: db_up
db_up:
	@$(COMPOSE) up -d postgres


.PHONY: db_stop
db_stop:
	@$(COMPOSE) stop postgres


.PHONY: db_restart
db_restart:
	@$(COMPOSE) restart postgres


.PHONY: obs_up
obs_up:
	@$(COMPOSE) up -d jaeger
	@echo "Jaeger UI: http://localhost:16686"


.PHONY: obs_stop
obs_stop:
	@$(COMPOSE) stop jaeger


.PHONY: obs_restart
obs_restart:
	@$(COMPOSE) restart jaeger


.PHONY: llm_up
llm_up:
	@$(COMPOSE) up -d ollama ollama-init
	@echo "Ollama API: http://localhost:11434"
	@echo "Ollama model ready: $(OLLAMA_DEFAULT_MODEL)"


.PHONY: llm_stop
llm_stop:
	@$(COMPOSE) stop ollama ollama-init


.PHONY: llm_restart
llm_restart:
	@$(COMPOSE) restart ollama ollama-init


.PHONY: stack_up
stack_up:
	@$(COMPOSE) up --build --detach


.PHONY: stack_stop
stack_stop:
	@$(COMPOSE) stop api postgres ollama ollama-init


.PHONY: stack_restart
stack_restart:
	@$(COMPOSE) restart api postgres ollama ollama-init


.PHONY: stack_down
stack_down:
	@$(COMPOSE) down --remove-orphans


## logs
.PHONY: logs_api
logs_api:
	@$(COMPOSE) logs --follow api


.PHONY: logs_db
logs_db:
	@$(COMPOSE) logs --follow postgres


.PHONY: logs_obs
logs_obs:
	@$(COMPOSE) logs --follow jaeger


.PHONY: logs_llm
logs_llm:
	@$(COMPOSE) logs --follow ollama


.PHONY: logs_stack
logs_stack:
	@$(COMPOSE) logs --follow


## cleanup
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
