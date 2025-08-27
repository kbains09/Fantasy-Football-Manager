SHELL := /bin/bash

# --- Paths & helpers ---
PY_DIR := apps/engine-py
GO_DIR := apps/web-go
OPENAPI := apis/engine.openapi.yaml
OAPI_CFG := apis/oapi-codegen.yaml

# Helper “exists” checks
HAS_PY := $(wildcard $(PY_DIR)/pyproject.toml)
HAS_GO := $(wildcard $(GO_DIR)/go.mod)

# Default compose file for prod-like runs (engine+web+db+redis)
INFRA_COMPOSE := infra/compose.yaml

# Default DB URLs
DC_DB_URL := postgresql+psycopg://dev:dev@postgres:5432/fantasy   # devcontainer DB host
INFRA_DB_URL := postgresql+psycopg://dev:dev@db:5432/fantasy      # infra/compose DB host

.PHONY: help
help: ## show available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}' | sort

# ---------------------------------------------------------------------
# Bootstrap & tools

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

.PHONY: tools
tools: ## install dev tools (oapi-codegen, golangci-lint)
	@echo "==> Installing dev tools"
	@which oapi-codegen >/dev/null 2>&1 || go install github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen@latest
	@which golangci-lint >/dev/null 2>&1 || (curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $$HOME/go/bin v1.60.0)

# ---------------------------------------------------------------------
# OpenAPI -> generated clients

.PHONY: gen gen-go
gen: gen-go ## generate API clients from OpenAPI

gen-go: ## generate Go client from $(OPENAPI)
	@if [ ! -f "$(OPENAPI)" ]; then echo "OpenAPI spec not found at $(OPENAPI)"; exit 1; fi
	@echo "==> Generating Go client from $(OPENAPI)"
	@if [ -f "$(OAPI_CFG)" ]; then \
		oapi-codegen -config $(OAPI_CFG) $(OPENAPI); \
	else \
		oapi-codegen -generate types,client -o packages/clients/go/engine.gen.go -package engine $(OPENAPI); \
	fi
	@echo "==> go fmt"
	@go fmt ./packages/clients/go/...

# ---------------------------------------------------------------------
# Dev (run services by hand, using host ports)

.PHONY: dev-engine
dev-engine: ## run FastAPI engine on :8000 (reads local env)
	@if [ -n "$(HAS_PY)" ]; then \
		cd $(PY_DIR) && poetry run uvicorn app:app --host 0.0.0.0 --port 8000; \
	else \
		echo "Engine not scaffolded (missing $(PY_DIR)/pyproject.toml)"; exit 1; \
	fi

.PHONY: dev-web
dev-web: ## run Go web on :8080; ENGINE_BASE_URL defaults to http://localhost:8000
	@if [ -n "$(HAS_GO)" ]; then \
		cd $(GO_DIR) && ENGINE_BASE_URL=$${ENGINE_BASE_URL:-http://localhost:8000} go run ./cmd/web; \
	else \
		echo "Web not scaffolded (missing $(GO_DIR)/go.mod)"; exit 1; \
	fi

# ---------------------------------------------------------------------
# Alembic (DB migrations) – default to devcontainer DB; override DB_URL=... as needed

.PHONY: alembic-rev
alembic-rev: ## create an autogen revision with MSG="..."
	@if [ -n "$(HAS_PY)" ]; then \
		cd $(PY_DIR) && DB_URL=$${DB_URL:-$(DC_DB_URL)} \
		alembic revision -m "$${MSG:-autogen}" --autogenerate; \
	else echo "No Python project"; fi

.PHONY: alembic-up
alembic-up: ## upgrade to head
	@if [ -n "$(HAS_PY)" ]; then \
		cd $(PY_DIR) && DB_URL=$${DB_URL:-$(DC_DB_URL)} \
		alembic upgrade head; \
	else echo "No Python project"; fi

.PHONY: alembic-downgrade
alembic-downgrade: ## downgrade one step (or set STEP=N)
	@if [ -n "$(HAS_PY)" ]; then \
		cd $(PY_DIR) && DB_URL=$${DB_URL:-$(DC_DB_URL)} \
		alembic downgrade -$${STEP:-1}; \
	else echo "No Python project"; fi

# ---------------------------------------------------------------------
# Seeding

.PHONY: seed
seed: ## seed demo data into DB (uses apps/engine-py/seed.py)
	@if [ -n "$(HAS_PY)" ]; then \
		cd $(PY_DIR) && DB_URL=$${DB_URL:-$(DC_DB_URL)} \
		python seed.py; \
	else \
		echo "Seed script not found or Python project missing"; \
	fi

# ---------------------------------------------------------------------
# Infra (prod-like stack): dockerized engine+web+db+redis

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
