# FantasyManager

[![License](https://img.shields.io/github/license/kbains09/FantasyManager.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Go](https://img.shields.io/badge/go-1.22-blue.svg)
![Postgres](https://img.shields.io/badge/db-PostgreSQL-informational.svg)
![Devcontainer](https://img.shields.io/badge/devcontainer-ready-success.svg)

FantasyManager is a **full-stack fantasy football platform** that manages leagues, teams, and rosters — and powers **trade and free agent suggestions** using player valuations and positional scarcity analysis.

---

## **Table of Contents**

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Development Workflow](#development-workflow)
- [Current Limitations](#current-limitations)
- [Roadmap](#roadmap)
- [Design Notes](#design-notes)
- [Contributing](#contributing)
- [License](#license)

---

## **Features**

### **Currently Implemented**

- **ESPN League Integration** — Sync teams, rosters, and players from your ESPN fantasy league
- **Player Valuation Engine** — VORP (Value Over Replacement Player) calculations with positional scarcity adjustments
- **Lineup Optimizer** — Recommends optimal starting lineup based on projected value
- **Trade Suggestions** — Identifies beneficial 1-for-1 trade opportunities across league opponents
- **Free Agent Recommendations** — Ranks available players by improvement to your team
- **Background Job Queue** — Async valuation computation with job status tracking
- **OpenAPI-First Design** — Complete spec with auto-generated Go client SDK
- **Devcontainer Environment** — Zero-config development with Python, Go, and Postgres

### **Planned / Roadmap**

- Multi-player trade package suggestions
- Real projection data integration (FantasyPros, ESPN projections)
- Waiver priority and FAAB bid recommendations
- Web UI dashboard (Go + HTMX)
- Yahoo/Sleeper league integrations
- CI/CD pipelines

---

## **Architecture**

```mermaid
flowchart LR
  subgraph Client Layer
    UI[Web UI]
    GoClient[Go Client SDK]
    CLI[CLI Tools]
  end

  subgraph Engine Layer
    API[Engine API<br/>FastAPI]
    Logic[Domain Logic<br/>valuation, trades, lineup]
    ESPN[ESPN Adapter]
  end

  subgraph Data Layer
    Store[In-Memory Store<br/>Demo Mode]
    DB[(PostgreSQL<br/>Production)]
  end

  UI -->|HTTP/JSON| API
  GoClient -->|HTTP/JSON| API
  CLI -->|HTTP/JSON| API

  API --> Logic
  API --> ESPN
  Logic --> Store
  Logic -.->|Future| DB
```

**Components:**

- **Engine (Python/FastAPI)** — Core domain logic and HTTP API
- **Go Client SDK** — Type-safe client generated from OpenAPI spec
- **ESPN Adapter** — Pulls league data from ESPN Fantasy API
- **Data Store** — In-memory for demos; SQLAlchemy models ready for production

---

## **Tech Stack**

| Layer | Technology |
|-------|------------|
| Backend | Python 3.13, FastAPI, Pydantic |
| Client SDK | Go 1.22, oapi-codegen |
| Database | PostgreSQL (models defined, optional for demo) |
| External APIs | ESPN Fantasy API via `espn-api` |
| Tooling | Docker, Devcontainers, Poetry, Make |

---

## **Getting Started**

### Prerequisites

- Docker & Docker Compose
- Visual Studio Code with [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
- `make` installed on your system

### Clone the Repository

```bash
git clone https://github.com/kbains09/FantasyManager.git
cd FantasyManager
```

### Open in Devcontainer

1. Open the folder in VS Code
2. Click "Reopen in Container" when prompted (or run `Dev Containers: Reopen in Container` from command palette)
3. Wait for container to build — this installs Python 3.13, Go 1.22, Postgres, and all dependencies

### Bootstrap the Environment

Inside the devcontainer terminal:

```bash
make bootstrap
```

### Running the Engine

```bash
# Via Makefile (recommended)
make engine/run

# Or directly
cd apps/engine-py
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Base:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **Health Check:** `GET /v1/health` → `{"ok": true}`

### Connect Your ESPN League (Optional)

To use real league data instead of mock data:

1. Create `apps/engine-py/.env`:
```env
ESPN_LEAGUE_ID=12345678
ESPN_YEAR=2024
ESPN_S2=your_espn_s2_cookie      # Required for private leagues
ESPN_SWID={your-swid-guid}       # Required for private leagues
```

2. Sync your league:
```bash
# Check connection
curl http://localhost:8000/v1/sync/espn/check

# Full sync
curl -X POST http://localhost:8000/v1/sync/espn/full
```

---

## **Configuration**

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ESPN_LEAGUE_ID` | Your ESPN league ID | For ESPN sync |
| `ESPN_YEAR` | Season year (e.g., 2024) | For ESPN sync |
| `ESPN_S2` | ESPN authentication cookie | Private leagues |
| `ESPN_SWID` | ESPN user identifier | Private leagues |
| `ESPN_MY_TEAM_ID` | Manual team ID override | Optional |
| `DB_URL` | PostgreSQL connection string | Optional (uses mock data if not set) |

### Default Values (Devcontainer)

```
Postgres → postgresql://dev:dev@postgres:5432/fantasy
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for full details.

---

## **Project Structure**

```
.devcontainer/            # Devcontainer configuration
apis/                     # OpenAPI specifications
  engine.openapi.yaml     # Engine API spec
apps/
  engine-py/              # Python backend
    adapters/espn/        # ESPN API integration
    db/                   # SQLAlchemy models
    jobs/                 # Background job queue
    services/             # Domain logic
      valuation.py        # VORP calculations
      lineup.py           # Lineup optimization
      recommend_fa.py     # Free agent suggestions
      recommend_trade.py  # Trade suggestions
    routes_*.py           # API route handlers
    main.py               # FastAPI application
  web-go/                 # Go web frontend (scaffolded)
infra/                    # Docker Compose for deployment
packages/
  clients/go/             # Generated Go client SDK
Makefile                  # Build automation
```

---

## **API Endpoints**

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/health` | Health check |
| `GET` | `/v1/players` | List players with filters |
| `GET` | `/v1/teams/{id}` | Get team roster and valuations |
| `GET` | `/v1/projections/sources` | List projection sources |

### Recommendations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/recommend/free-agents?team_id=X` | Get FA pickup suggestions |
| `POST` | `/v1/recommend/trades` | Get trade suggestions |
| `POST` | `/v1/lineup/recommend` | Get optimal lineup |

### ESPN Integration

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/sync/espn/check` | Verify ESPN connection |
| `POST` | `/v1/sync/espn/full` | Full league sync |
| `POST` | `/v1/sync/espn/delta` | Incremental sync |
| `GET` | `/v1/me/team` | Get your team ID |

### Compute Jobs

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/compute/valuations` | Trigger valuation job |
| `GET` | `/v1/jobs/{job_id}` | Get job status |

Full API documentation available at `http://localhost:8000/docs` when running.

---

## **Development Workflow**

### Useful Commands

```bash
make bootstrap      # Install dependencies
make engine/run     # Run Python API server
make gen            # Regenerate Go client from OpenAPI
make lint           # Run linters (ruff + go vet)
make test           # Run test suites
make db/up          # Run database migrations
```

### Making API Changes

1. Update `apis/engine.openapi.yaml`
2. Run `make gen` to regenerate Go client
3. Implement the endpoint in `apps/engine-py/routes_*.py`
4. Add/update tests
5. Run `make lint test` before committing

---

## **Current Limitations**

This is an MVP/portfolio project with intentional simplifications:

| Limitation | Reason | Future Plan |
|------------|--------|-------------|
| **Mock data by default** | Zero-setup demos without DB | ESPN sync populates real data |
| **1-for-1 trades only** | Keeps recommendations explainable | Multi-player packages planned |
| **Mock projections** | No external API keys required | FantasyPros integration planned |
| **No authentication** | Single-user local use | OAuth with ESPN/Google planned |
| **In-memory job queue** | Simpler than Celery for MVP | Redis-backed queue planned |

---

## **Roadmap**

### Near Term
- [ ] Multi-player trade suggestions
- [ ] Persistent database integration
- [ ] Basic test suite

### Medium Term
- [ ] Real projection data (FantasyPros API)
- [ ] Web UI with HTMX
- [ ] FAAB bid recommendations
- [ ] GitHub Actions CI

### Long Term
- [ ] Yahoo/Sleeper integrations
- [ ] ML-powered trade acceptance prediction
- [ ] Automated lineup optimization alerts
- [ ] Mobile app

---

## **Design Notes**

### Goals

- **Domain-First** — Model fantasy football properly, not as a script collection
- **API-First** — OpenAPI spec is source of truth; clients are generated
- **Portable Engine** — Core logic usable from CLI, web, mobile, or bots

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Python for Engine | Rich ecosystem for data/ML, fast prototyping |
| Go for Clients | Type safety, single binary deployment |
| In-memory default | Instant demos without infrastructure |
| ESPN first | Most popular platform, good unofficial API |

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| ESPN API rate limits | Caching, exponential backoff |
| Complex trade logic | Modular services, extensive testing |
| Scope creep | Focus on differentiation (recommendations) |

See [docs/DESIGN_NOTES.md](docs/DESIGN_NOTES.md) for detailed architecture discussion.

---

## **Contributing**

Contributions welcome!

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run `make lint test`
5. Commit: `git commit -m "Add feature"`
6. Push and open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## **License**

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0).  
See the [LICENSE](LICENSE) file for details.