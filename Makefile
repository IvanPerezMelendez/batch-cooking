.PHONY: help run_local test lint format check_all docker_up docker_down docker_logs

PYTHON := uv run
FASTAPI := fastapi
SRC := src/main.py

help:
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

test:
	$(PYTHON) pytest tests/

docker_up:
	docker compose -f docker-compose.yaml up -d

docker_down:
	docker compose -f docker-compose.yaml down

docker_logs:
	docker compose -f docker-compose.yaml logs -f

# Alembic commands (developers)
alembic_autogenerate:
	@printf "Enter migration description: "; \
	read desc; \
	uv run alembic revision --autogenerate \
	--rev-id $$(date +%Y%m%d%H%M%S) \
	-m "$$desc"

alembic_head:
	uv run alembic upgrade head

alembic_merge_heads:
	uv run alembic merge heads \
	--rev-id $$(date +%Y%m%d%H%M%S) \
	-m "merge heads"

run_local:
	uv run fastapi dev src/batch_cooking/main.py
