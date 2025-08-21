PY = cd apps/engine-py && poetry
GO = cd apps/web-go

export COMPOSE_PROFILES ?= dev

.PHONY: bootstrap
bootstrap: ## one-time: install toolchains
	@echo "Setting up Python and Go deps"
	cd apps/engine-py && poetry install
	cd apps/web-go && go mod tidy

.PHONY: gen
gen: ## generate API clients from OpenAPI
	oapi-codegen -generate types,client -o packages/clients/go/engine.gen.go -package engine \
		apis/engine.openapi.yaml
	# (optional) python client gen step here

.PHONY: db-up
db-up:
	docker compose -f infra/compose.yaml up -d db redis
	sleep 2
	# Run Alembic migrations
	cd infra/db && alembic upgrade head

.PHONY: up
up: ## run full stack (db, redis, engine, web)
	docker compose -f infra/compose.yaml up --build

.PHONY: down
down:
	docker compose -f infra/compose.yaml down -v

.PHONY: lint
lint:
	$(PY) run ruff check .
	cd apps/web-go && golangci-lint run

.PHONY: test
test:
	$(PY) run pytest -q
	cd apps/web-go && go test ./...

.PHONY: seed
seed:
	python ops/scripts/seed_league.py --file examples/league.json
