# Contributing to FantasyManager

Thank you for your interest in contributing! FantasyManager is a modern, API-first fantasy football platform. Contributions of all kinds are welcome — code, documentation, testing, or feature ideas.

---

## 1. Code of Conduct

By contributing, you agree to:

- Be constructive and respectful
- Ask questions early
- Provide clear explanations for changes
- Support newcomers to the project

---

## 2. Getting Started

### 2.1 Fork the Repository

```bash
# Fork via GitHub UI, then:
git clone https://github.com/<your-username>/FantasyManager.git
cd FantasyManager
```

### 2.2 Open in Devcontainer

FantasyManager uses a devcontainer for consistent development environments.

1. Open the project in VS Code
2. Install the "Dev Containers" extension if needed
3. Click "Reopen in Container" when prompted
4. Wait for the container to build (installs Python 3.13, Go 1.22, Postgres)

### 2.3 Bootstrap

```bash
make bootstrap
```

This installs Python dependencies (Poetry) and Go modules.

---

## 3. Development Workflow

### 3.1 Create a Feature Branch

```bash
git checkout -b feature/my-new-feature
```

Use clear branch names:
- `feature/add-yahoo-adapter`
- `fix/espn-sync-timeout`
- `docs/update-api-examples`
- `test/add-valuation-tests`

### 3.2 Makefile Commands

```bash
make bootstrap      # Install dependencies
make engine/run     # Run FastAPI server on :8000
make gen            # Regenerate Go client from OpenAPI
make lint           # Run ruff (Python) + go vet
make test           # Run test suites
make db/up          # Run Alembic migrations
```

### 3.3 Running the Engine

```bash
# Via Makefile
make engine/run

# Or directly
cd apps/engine-py
poetry run uvicorn main:app --reload --port 8000
```

API available at `http://localhost:8000/docs`

---

## 4. Coding Standards

### 4.1 Python (Engine)

- **Style:** PEP 8, enforced by `ruff`
- **Imports:** Explicit imports, no wildcards
- **Type hints:** Required for public functions
- **Docstrings:** Required for routes and services

```python
# Good
from typing import Optional
from services.valuation import compute_vorp_for_week

def get_team_route(team_id: str, week: Optional[int] = None) -> dict:
    """Get team roster with valuations."""
    ...

# Bad
from services import *  # No wildcards
def get_team(id, w):    # Missing types
    ...
```

### 4.2 Go (Client SDK)

- **Style:** Standard `go fmt`
- **Generated code:** Don't edit `engine.gen.go` directly
- **Tests:** Add `*_test.go` files for new functionality

---

## 5. API Guidelines (OpenAPI First)

FantasyManager uses an OpenAPI-first workflow. **Always update the spec before implementing.**

### Adding/Modifying Endpoints

1. **Update the spec:** `apis/engine.openapi.yaml`
2. **Regenerate client:** `make gen`
3. **Implement route:** `apps/engine-py/routes_*.py`
4. **Add tests**

### Pull Request Requirements

PRs that modify API endpoints must include:
- [ ] OpenAPI spec changes
- [ ] Regenerated Go client (`make gen`)
- [ ] Python implementation
- [ ] Tests (if applicable)

---

## 6. Project Structure

```
apis/
  engine.openapi.yaml     # API specification (edit this first)

apps/engine-py/
  main.py                 # FastAPI app entry point
  routes_*.py             # HTTP route handlers
  services/               # Domain logic
    valuation.py          # VORP calculations
    lineup.py             # Lineup optimization
    recommend_fa.py       # Free agent suggestions
    recommend_trade.py    # Trade suggestions
    mock_data.py          # In-memory data store
  adapters/espn/          # ESPN integration
  db/                     # SQLAlchemy models
  jobs/                   # Background job queue

packages/clients/go/
  engine.gen.go           # Generated Go client (don't edit)
```

---

## 7. Database Changes

If your change requires schema modifications:

### Using Alembic (Recommended)

```bash
cd apps/engine-py

# Create migration
poetry run alembic revision --autogenerate -m "add_new_field"

# Apply migration
poetry run alembic upgrade head
```

Migrations are stored in `apps/engine-py/alembic/versions/`.

### Guidelines

- Make migrations reversible when possible
- Test migrations locally before pushing
- Don't modify existing migrations that have been merged

---

## 8. Testing

### Python Tests

```bash
cd apps/engine-py
poetry run pytest
```

Tests should be in `apps/engine-py/tests/`.

**Guidelines:**
- One concept per test file
- Use descriptive test names
- Mock external APIs (ESPN)
- Keep tests focused and fast

### Go Tests

```bash
cd packages/clients/go
go test ./...
```

---

## 9. Submitting a Pull Request

### Before Submitting

```bash
make lint    # Fix any linting errors
make test    # Ensure tests pass
make gen     # Regenerate client if API changed
```

### PR Description Template

```markdown
## What

Brief description of changes.

## Why

Problem being solved or feature being added.

## How

Technical approach taken.

## Testing

How you tested the changes.

## Checklist

- [ ] Linting passes (`make lint`)
- [ ] Tests pass (`make test`)
- [ ] OpenAPI spec updated (if API changed)
- [ ] Go client regenerated (if API changed)
- [ ] Documentation updated (if needed)
```

---

## 10. Reporting Bugs

Open a GitHub Issue with:

- **Description:** What's broken
- **Steps to reproduce:** Minimal example
- **Expected behavior:** What should happen
- **Actual behavior:** What happens instead
- **Environment:** OS, Python version, etc.
- **Logs:** Relevant error messages

---

## 11. Requesting Features

Open a GitHub Issue with:

- **Problem:** What you're trying to solve
- **Proposed solution:** Your idea
- **Alternatives:** Other approaches considered
- **Context:** Why this matters (use case)

We evaluate features based on:
- Value to the platform
- Consistency with existing design
- Implementation complexity

---

## 12. Project Philosophy

Contributions should align with these principles:

- **API-first:** Spec before implementation
- **Separation of concerns:** Routes → Services → Data
- **Typed clients:** Go SDK generated from OpenAPI
- **Developer-friendly:** Devcontainer, Makefile, good docs
- **Pragmatic:** Working features over perfect architecture

Pull requests that add unnecessary complexity may be declined or simplified.

---

## 13. Questions?

- Open a GitHub Issue for technical questions
- Check existing issues for similar questions
- Review the [Design Notes](docs/DESIGN_NOTES.md) for architectural context

Thank you for contributing!