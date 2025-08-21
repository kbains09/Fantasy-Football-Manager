SHELL := /bin/bash

# --- Paths & helpers ---
PY_DIR := apps/engine-py
GO_DIR := apps/web-go
OPENAPI := apis/engine.openapi.yaml

# Helper “exists” checks
HAS_PY := $(wildcard $(PY_DIR)/pyproject.toml)
HAS_GO := $(wildcard $(GO_DIR)/go.mod)

# Default compose file for prod-like runs (engine+web+db+redis)
INFRA_COMPOSE := infra/compose.yaml

.PHONY: help
help: ## show available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}' | sort

# ---------------------------------------------------------------------

.PHONY: bootstrap
bootstrap: ## install deps if present (Poetry + Go)
	@echo "==> Bootstrapping"
	@if [ -n "$(HAS_PY)" ]; then \
		echo " • Python deps (Poetry)"; \
		cd $(PY_DIR) && poetry install --no-interaction; \
	else \
		echo " • Skipping Python: $(PY_DIR)/pyproject.toml not found"; \
	fi
	@if [ -n "$(HAS_GO)" ]; then \
		echo " • Go deps (go mod tidy)"; \
		cd $(GO_DIR) && go mod tidy; \
	else \
		echo " • Skipping Go: $(GO_DIR)/go.mod not found"; \
	fi

.PHONY: gen
gen: ## generate API clients from OpenAPI
	@if [ -f "$(OPENAPI)" ]; then \
		echo "==> Generating Go client from $(OPENAPI)"; \
		oapi-codegen -generate types,client -o packages/clients/go/engine.gen.go -package engine $(OPENAPI); \
	else \
		echo "OpenAPI spec not found at $(OPENAPI)"; exit 1; \
	fi

# ---------------------------------------------------------------------
# Devcontainer local dev (manual app run). Postgres & Redis are started
# by .devcontainer/docker-compose.yaml. Use these helpers to run apps.

.PHONY: engine
engine: ## run FastAPI engine in dev (uses current env)
	@if [ -n "$(HAS_PY)" ]; then \
		cd $(PY_DIR) && poetry run uvicorn main:app --host 0.0.0.0 --port 8000; \
	else \
		echo "Engine not scaffolded (missing $(PY_DIR)/pyproject.toml)"; exit 1; \
	fi

.PHONY: web
web: ## run Go web in dev (uses current env)
	@if [ -n "$(HAS_GO)" ]; then \
		cd $(GO_DIR) && go run ./cmd/web; \
	else \
		echo "Web not scaffolded (missing $(GO_DIR)/go.mod)"; exit 1; \
	fi

# ---------------------------------------------------------------------
# Infra (prod-like stack) – builds and runs dockerized engine+web+db+redis

.PHONY: infra-up
infra-up: ## docker compose up (engine, web, db, redis)
	@if [ -f "$(INFRA_COMPOSE)" ]; then \
		docker compose -f $(INFRA_COMPOSE) up --build -d; \
	else \
		echo "Missing $(INFRA_COMPOSE)"; exit 1; \
	fi

.PHONY: infra-down
infra-down: ## docker compose down -v
	@if [ -f "$(INFRA_COMPOSE)" ]; then \
		docker compose -f $(INFRA_COMPOSE) down -v; \
	else \
		echo "Missing $(INFRA_COMPOSE)"; exit 1; \
	fi

.PHONY: infra-logs
infra-logs: ## tail logs from infra compose
	@if [ -f "$(INFRA_COMPOSE)" ]; then \
		docker compose -f $(INFRA_COMPOSE) logs -f; \
	else \
		echo "Missing $(INFRA_COMPOSE)"; exit 1; \
	fi

# ---------------------------------------------------------------------
# Quality

.PHONY: lint
lint: ## run linters when available
	@if [ -n "$(HAS_PY)" ]; then \
		cd $(PY_DIR) && poetry run ruff check .; \
	else \
		echo "Skipping Python lint"; \
	fi
	@if [ -n "$(HAS_GO)" ]; then \
		cd $(GO_DIR) && golangci-lint run || echo 'Install golangci-lint to enable Go lint'; \
	else \
		echo "Skipping Go lint"; \
	fi

.PHONY: test
test: ## run tests when available
	@if [ -n "$(HAS_PY)" ]; then \
		cd $(PY_DIR) && poetry run pytest -q || echo 'No Python tests yet'; \
	else \
		echo "Skipping Python tests"; \
	fi
	@if [ -n "$(HAS_GO)" ]; then \
		cd $(GO_DIR) && go test ./... || echo 'No Go tests yet'; \
	else \
		echo "Skipping Go tests"; \
	fi

# ---------------------------------------------------------------------

.PHONY: seed
seed: ## seed demo data (if script exists)
	@if [ -f "ops/scripts/seed_league.py" ]; then \
		python ops/scripts/seed_league.py --file examples/league.json; \
	else \
		echo "Seed script not found"; \
	fi
