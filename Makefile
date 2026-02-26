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


.PHONY: lint
lint:
	@$(VENV_PYTHON) -m ruff check $(APP_DIR) $(TEST_DIR)
	@$(VENV_PYTHON) -m ruff format --check $(APP_DIR) $(TEST_DIR)


.PHONY: format
format:
	@$(VENV_PYTHON) -m ruff check --fix $(APP_DIR) $(TEST_DIR)
	@$(VENV_PYTHON) -m ruff format $(APP_DIR) $(TEST_DIR)


.PHONY: alembic_init
alembic_init:
	@$(VENV_PYTHON) -m alembic init migrations


.PHONY: alembic_upgrade
alembic_upgrade:
	@$(VENV_PYTHON) -m alembic upgrade head


.PHONY: alembic_migrate
alembic_migrate:
	@$(VENV_PYTHON) -m alembic revision --autogenerate -m "$(msg)"


.PHONY: run_test
run_test:
	@$(VENV_PYTHON) -m pytest $(TEST_DIR)


.PHONY: run_dev
run_dev:
	@$(VENV_PYTHON) -m uvicorn $(API_MODULE) \
	--host $(API_HOST) \
	--port $(API_PORT) \
	--reload


.PHONY: run_prd
run_prd:
	@$(VENV_PYTHON) -m uvicorn $(API_MODULE) \
	--host $(API_HOST) \
	--port $(API_PORT) \
	--workers $(API_WORKERS)

.PHONY: db_up
db_up:
	@$(COMPOSE) up -d postgres


.PHONY: db_down
db_down:
	@$(COMPOSE) stop postgres


.PHONY: obs_up
obs_up:
	@$(COMPOSE) up -d jaeger
	@echo "Jaeger UI: http://localhost:16686"


.PHONY: obs_down
obs_down:
	@$(COMPOSE) stop jaeger


.PHONY: llm_up
llm_up:
	@$(COMPOSE) up -d ollama ollama-init
	@echo "Ollama API: http://localhost:11434"
	@echo "Ollama model ready: $(OLLAMA_DEFAULT_MODEL)"


.PHONY: llm_down
llm_down:
	@$(COMPOSE) stop ollama ollama-init


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
