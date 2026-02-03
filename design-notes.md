# FantasyManager – Design Notes

This document provides an overview of the architectural goals, key design decisions, and trade-offs behind FantasyManager. It's intended for collaborators, technical reviewers, and future maintainers.

---

## 1. Overview

FantasyManager is a **modular fantasy football platform** designed around an API-first architecture. The Python Engine handles all domain logic (valuations, trades, lineups), while a Go client SDK enables type-safe consumption from CLIs, web apps, or automation tools.

**What's Working Today:**
- ESPN league synchronization
- Player valuation (VORP calculations)
- Lineup optimization
- Trade and free agent recommendations
- Background job processing
- OpenAPI-driven client generation

---

## 2. System Goals

### Primary Goals

| Goal | Status | Notes |
|------|--------|-------|
| Reusable Engine | ✅ Done | All domain logic in Python, consumable via HTTP |
| API-first development | ✅ Done | OpenAPI spec generates Go client |
| Strong data modeling | ⚠️ Partial | SQLAlchemy models defined, routes use in-memory store |
| Developer-friendly environment | ✅ Done | Devcontainer with zero-config setup |
| Extensibility for ML | 🔮 Future | Architecture supports it, not yet implemented |

### Non-Goals (Intentional Exclusions)

- **Full ESPN clone** — Focus on recommendations, not replicating ESPN's UI
- **Multi-user SaaS** — Single-user local tool for now
- **Real-time scoring** — Batch updates, not live websockets

---

## 3. Architecture

### Current State

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Swagger UI │  │  Go Client  │  │    cURL     │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
└─────────┼────────────────┼────────────────┼────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                   Engine (FastAPI)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │                    Routes                        │   │
│  │  /health  /players  /teams  /recommend  /sync   │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                                │
│  ┌─────────────────────▼───────────────────────────┐   │
│  │                  Services                        │   │
│  │  valuation.py  lineup.py  recommend_*.py        │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                                │
│  ┌─────────────────────▼───────────────────────────┐   │
│  │               Data Layer                         │   │
│  │  ┌─────────────┐       ┌─────────────────────┐  │   │
│  │  │ mock_data.py│◄─────►│ ESPN Adapter        │  │   │
│  │  │ (in-memory) │       │ (populates store)   │  │   │
│  │  └─────────────┘       └─────────────────────┘  │   │
│  │         │                                        │   │
│  │         ▼ (future)                               │   │
│  │  ┌─────────────┐                                 │   │
│  │  │ PostgreSQL  │ (models defined, not wired)    │   │
│  │  └─────────────┘                                 │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Location |
|-----------|---------------|----------|
| **Routes** | HTTP endpoints, request validation | `routes_*.py` |
| **Services** | Domain logic (stateless) | `services/` |
| **Adapters** | External API integration | `adapters/espn/` |
| **Data Store** | State management | `services/mock_data.py` |
| **Models** | Database schema (future) | `db/models.py` |
| **Jobs** | Background processing | `jobs/` |

---

## 4. Key Design Decisions

### 4.1 Python for Engine

**Rationale:**
- Fast prototyping and iteration
- Rich ecosystem for data manipulation (pandas-ready for projections)
- FastAPI provides excellent developer experience (auto-docs, validation)
- Easy path to ML integration (scikit-learn, pytorch)

**Trade-off:** Lower raw performance than Go, but acceptable for this use case.

### 4.2 Go for Client SDK

**Rationale:**
- Compile-time type safety catches API contract mismatches
- Single binary deployment for CLI tools
- Natural fit for future HTMX web frontend
- Generated automatically from OpenAPI (zero maintenance)

**Trade-off:** Two languages in repo, but clear separation of concerns.

### 4.3 In-Memory Store (Demo Mode)

**Rationale:**
- Zero-setup demos — works without database configuration
- ESPN sync populates the store with real data
- Faster iteration during development
- SQLAlchemy models exist for production migration path

**Trade-off:** Data doesn't persist across restarts. Acceptable for portfolio/demo.

### 4.4 OpenAPI-First Development

**Rationale:**
- Single source of truth for API contract
- Auto-generated Go client stays in sync
- Swagger UI for free
- Forces thinking about API design before implementation

**Workflow:**
1. Design endpoint in `apis/engine.openapi.yaml`
2. Run `make gen` to update Go client
3. Implement Python route
4. Contract guaranteed to match

### 4.5 VORP-Based Valuations

**Rationale:**
- Industry-standard fantasy football metric
- Accounts for positional scarcity (a TE5 is more valuable than WR25)
- Simple to explain to users
- Extensible with real projection data

**Current Implementation:**
- Mock projections (deterministic, based on position)
- Replacement level calculated per league settings
- VORP = Projected Points - Replacement Level

### 4.6 Simple Trade Logic (1-for-1)

**Rationale:**
- Explainable recommendations ("trade your RB3 for their WR2")
- Easier to validate fairness
- Foundation for multi-player packages later

**Trade-off:** Misses complex multi-player deals. Acceptable for MVP.

---

## 5. Domain Model

### Core Entities

```
League (1) ──────┬────── (*) Team
                 │
Team (1) ────────┼────── (*) RosterSpot ────── (1) Player
                 │
Player (1) ──────┼────── (*) Valuation (per week, per source)
                 │
League (1) ──────┴────── (*) Transaction (audit log)
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **VORP** | Value Over Replacement Player — how much better than a waiver pickup |
| **Replacement Level** | The Nth-best player at a position (N = starters × teams) |
| **Positional Scarcity** | Positions with fewer startable players have higher value |
| **Slot** | Lineup position (QB, RB, WR, TE, FLEX, BN, IR) |

---

## 6. Current Limitations & Future Work

### Intentional MVP Simplifications

| Limitation | Reason | Future Plan |
|------------|--------|-------------|
| In-memory data | Zero-setup demos | Wire SQLAlchemy models to routes |
| Mock projections | No API keys needed | Integrate FantasyPros or ESPN projections |
| 1-for-1 trades | Simpler to explain | Knapsack optimization for packages |
| No auth | Single-user tool | OAuth with ESPN/Google |
| Threading job queue | Simpler than Celery | Redis-backed queue if needed |

### Database Migration Path

The SQLAlchemy models in `db/models.py` mirror the in-memory structures:

```python
# Already defined, just need to wire to routes:
class Player(Base):
    id: Mapped[str]
    name: Mapped[str]
    pos: Mapped[str]
    team: Mapped[str]
    
class Valuation(Base):
    player_id: Mapped[str]
    week: Mapped[int]
    vorp: Mapped[float]
```

To migrate:
1. Update routes to accept `Session` dependency
2. Replace `mock_data` calls with `Store` methods
3. Run Alembic migrations

---

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ESPN API changes | Sync breaks | Adapter pattern isolates changes |
| ESPN rate limits | Slow/blocked sync | Caching, backoff (planned) |
| Scope creep | Never ships | Focus on recommendations as differentiator |
| Complex trade logic | Hard to maintain | Strict service boundaries, tests |
| Stale projections | Bad recommendations | Show projection source + date |

---

## 8. Why This Architecture?

This design optimizes for:

1. **Portfolio Demonstration** — Clean separation, documented decisions, working features
2. **Extensibility** — Easy to add Yahoo/Sleeper adapters, ML models, web UI
3. **Developer Experience** — Devcontainer, Makefile, Swagger UI
4. **Pragmatism** — Mock data for demos, real ESPN data when configured

The architecture supports evolution from a portfolio project to a production tool without rewrites.

---

## 9. Document History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2024-11-23 | Initial design notes |
| 1.1 | 2025-02-02 | Updated to reflect current implementation state |