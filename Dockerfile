# BUILDER: installs dependencies
FROM python:3.13-slim AS builder

# PYTHONDONTWRITEBYTECODE=1
#     - Prevents .pyc generation during build/install steps.
#     - Reduces unnecessary filesystem writes/layer noise.
# PYTHONUNBUFFERED=1
#     - Forces stdout/stderr flush immediately.
#     - Better for CI/build logs.
# PIP_NO_CACHE_DIR=1
#     - Prevents pip wheel/download cache from being stored in image layers.
#     - Reduces layer size.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --only main --no-interaction --no-ansi


# RUNTIME: runs the app with a smaller/cleaner image
FROM python:3.13-slim AS runtime

# PYTHONDONTWRITEBYTECODE=1
#     - Avoids runtime .pyc file writes.
#     - Good for immutable/containerized filesystems.
# PYTHONUNBUFFERED=1
#     - Makes app logs appear immediately in docker logs.
#     - Important for observability and debugging in containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app app

COPY --from=builder /usr/local /usr/local
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
