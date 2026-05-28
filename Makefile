.DEFAULT_GOAL := help
COMPOSE := docker compose

.PHONY: help up down logs ps test test-backend test-frontend lint lint-backend lint-frontend spike-terrain seed-pilot-data clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

up: ## Build + start the walking-skeleton stack
	$(COMPOSE) up --build

down: ## Stop the stack
	$(COMPOSE) down

logs: ## Tail service logs
	$(COMPOSE) logs -f

ps: ## Show service status/health
	$(COMPOSE) ps

test: test-backend test-frontend ## Run all tests

test-backend: ## Backend pytest (inside the api image)
	cd backend && uv run pytest -q

test-frontend: ## Frontend vitest
	cd frontend && npm test

lint: lint-backend lint-frontend ## Lint + type-check everything

lint-backend: ## Ruff + mypy
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app geo

lint-frontend: ## ESLint + Prettier + tsc
	cd frontend && npm run lint && npx prettier --check "src/**/*.{ts,tsx}" && npx tsc --noEmit

spike-terrain: ## Run the terrain-shading benchmark on the committed Nepal fixture
	cd backend && uv run python -m geo.spike_terrain tests/fixtures/dem/nepal_aoi_clip_glo30.tif tests/fixtures/aoi/gulmi_test_polygon.geojson

seed-pilot-data: ## Fetch (or fall back to fixture) a pilot DEM, convert to COG, push to MinIO
	cd data-pipelines && uv run python -m ingest.fetch_dem --fallback-fixture

clean: ## Remove the stack + named volumes
	$(COMPOSE) down -v
