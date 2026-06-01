# MathBot — Developer Makefile
# Usage: make <target>
# On Windows, install Make via: winget install GnuWin32.Make
# Or use: python -m <command> directly

.PHONY: help dev stop test lint format typecheck migrate shell clean

# ── Default target ────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  MathBot Developer Commands"
	@echo "  ─────────────────────────────────────────────────────"
	@echo "  make dev        Start all services (Docker)"
	@echo "  make stop       Stop all services"
	@echo "  make test       Run all tests with coverage"
	@echo "  make lint       Run ruff linter"
	@echo "  make format     Auto-format with ruff"
	@echo "  make typecheck  Run mypy type checker"
	@echo "  make migrate    Run Alembic database migrations"
	@echo "  make shell      Open a Python shell inside the API container"
	@echo "  make clean      Remove all containers and volumes"
	@echo ""

# ── Docker commands ───────────────────────────────────────────────────────────
dev:
	docker compose up --build

stop:
	docker compose down

clean:
	docker compose down -v --remove-orphans

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v --cov=. --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

# ── Code quality ──────────────────────────────────────────────────────────────
lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy . --ignore-missing-imports

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

# ── Misc ─────────────────────────────────────────────────────────────────────
shell:
	docker compose exec api python
