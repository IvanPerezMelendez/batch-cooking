FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar dependencias primero (capa cacheada)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copiar el código
COPY src/ ./src/
COPY static/ ./static/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Instalar el paquete del proyecto
RUN uv sync --frozen --no-dev

EXPOSE 8000

# Migrar la BD y arrancar el servidor
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn batch_cooking.main:app --host 0.0.0.0 --port 8000 --workers 1"]
