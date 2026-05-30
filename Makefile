.DEFAULT_GOAL := help
COMPOSE := docker compose
COMPOSE_PROD := docker compose -f docker-compose.yml -f docker-compose.prod.yml

# GCP VM defaults (override via env, e.g. ZONE=asia-southeast1-b make vm-start).
INSTANCE_NAME ?= terrabean-demo
ZONE ?= asia-southeast1-a

.PHONY: help up down logs ps test test-backend test-frontend lint lint-backend lint-frontend spike-terrain seed-pilot-data seed-nepal validate clean deploy deploy-seed deploy-logs deploy-down vm-start vm-stop vm-ssh

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

seed-nepal: ## Seed ALL of Nepal: real Copernicus GLO-90 DEM + climate (CLIMATE_SOURCE=synthetic|real, default synthetic)
	cd data-pipelines && uv run python -m ingest.seed_pilot --version 2026.1 --region nepal --climate-source $(or $(CLIMATE_SOURCE),synthetic) $(SEED_ARGS)

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

# --- GCP demo deployment (single VM, Compose + Caddy) -------------------------
# See infra/gcp/README.md and docs/adr/0009-gcp-single-vm-demo-deployment.md.

deploy: ## On the VM: build + (re)start the production stack
	$(COMPOSE_PROD) up -d --build

deploy-down: ## On the VM: stop the production stack (data volumes survive)
	$(COMPOSE_PROD) down

deploy-logs: ## On the VM: tail production logs
	$(COMPOSE_PROD) logs -f

deploy-seed: ## On the VM: one-time seed of the pilot DEM + climate into MinIO + PostGIS
	$(COMPOSE_PROD) run --rm api python -m data_pipelines.ingest.seed_pilot --version 2026.1 || \
		(echo "fallback: running seed from a host-side data-pipelines venv"; \
		 cd data-pipelines && uv run python -m ingest.seed_pilot --version 2026.1)

vm-start: ## From your laptop: start the GCP VM
	gcloud compute instances start $(INSTANCE_NAME) --zone $(ZONE)
	@gcloud compute instances describe $(INSTANCE_NAME) --zone $(ZONE) --format='value(networkInterfaces[0].accessConfigs[0].natIP)' | awk '{print "External IP:",$$1," (update your A record if it changed)"}'

vm-stop: ## From your laptop: stop the GCP VM (compute charges pause, ~95% saving)
	gcloud compute instances stop $(INSTANCE_NAME) --zone $(ZONE)

vm-ssh: ## From your laptop: SSH into the GCP VM
	gcloud compute ssh $(INSTANCE_NAME) --zone $(ZONE)
