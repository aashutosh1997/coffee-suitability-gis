.DEFAULT_GOAL := help
COMPOSE := docker compose

.PHONY: help up down logs ps test test-backend test-frontend lint lint-backend lint-frontend spike-terrain seed-pilot-data seed-nepal validate clean

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

test-backend: ## Backend pytest (geo stack for the real engine)
	cd backend && uv run --extra geo pytest -q

test-frontend: ## Frontend vitest
	cd frontend && npm test

lint: lint-backend lint-frontend ## Lint + type-check everything

lint-backend: ## Ruff + mypy
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run --extra geo mypy app worker geo

lint-frontend: ## ESLint + Prettier + tsc
	cd frontend && npm run lint && npx prettier --check "src/**/*.{ts,tsx}" && npx tsc --noEmit

spike-terrain: ## Run the terrain-shading benchmark on the committed Nepal fixture
	cd backend && uv run --extra geo python -m geo.spike_terrain tests/fixtures/dem/nepal_aoi_clip_glo30.tif tests/fixtures/aoi/gulmi_test_polygon.geojson

seed-pilot-data: ## Seed the pilot DEM: fetch Copernicus (fixture fallback) -> COG -> MinIO -> provenance
	cd data-pipelines && uv run python -m ingest.seed_pilot --version 2026.1 $(SEED_ARGS)

seed-nepal: ## Seed ALL of Nepal: real Copernicus GLO-90 DEM + derived climate -> MinIO -> provenance
	cd data-pipelines && uv run python -m ingest.seed_pilot --version 2026.1 --region nepal $(SEED_ARGS)

validate: ## Validate the model against a ground-truth CSV (stack must be up + seeded)
	$(COMPOSE) exec api python -m app.validation.run \
		--plots /config/ground-truth/$(or $(PLOTS),synthetic_plots.csv) \
		--config /config/suitability/arabica-$(or $(CONFIG),2026.1).yaml \
		--out /tmp/phase3
	@mkdir -p docs/phase-3
	@$(COMPOSE) cp api:/tmp/phase3/. docs/phase-3/
	@echo "validate: reports copied to docs/phase-3/"

clean: ## Remove the stack + named volumes
	$(COMPOSE) down -v
