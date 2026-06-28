.PHONY: help db-up db-down migrate seed api web test install

help:
	@echo "FADA EA v3 — Gêmeo Digital da Soja"
	@echo ""
	@echo "  make install   instala dependências (engine, api, web)"
	@echo "  make db-up      sobe o PostGIS (docker compose)"
	@echo "  make db-down    derruba o PostGIS"
	@echo "  make migrate    aplica as migrations (Alembic)"
	@echo "  make seed       popula cultivares + fazenda-demo"
	@echo "  make api        roda a API (FastAPI, :8000)"
	@echo "  make web        roda o frontend (Next.js, :3000)"
	@echo "  make test       roda os testes do motor agronômico"

install:
	cd packages/agro_engine && uv venv .venv && . .venv/bin/activate && uv pip install -e ".[dev]"
	cd apps/api && uv venv .venv && . .venv/bin/activate && uv pip install -e . -e ../../packages/agro_engine
	cd apps/web && pnpm install

db-up:
	docker compose -f infra/docker-compose.yml up -d

db-down:
	docker compose -f infra/docker-compose.yml down

migrate:
	cd apps/api && . .venv/bin/activate && alembic upgrade head

seed:
	cd apps/api && . .venv/bin/activate && python seed.py

api:
	cd apps/api && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && pnpm dev

test:
	cd packages/agro_engine && . .venv/bin/activate && python -m pytest -q
