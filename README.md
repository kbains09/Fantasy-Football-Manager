# FantasyManager

[![License](https://img.shields.io/github/license/kbains09/FantasyManager.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Go](https://img.shields.io/badge/go-1.22-blue.svg)
![Postgres](https://img.shields.io/badge/db-PostgreSQL-informational.svg)
![Redis](https://img.shields.io/badge/cache-Redis-red.svg)
![Devcontainer](https://img.shields.io/badge/devcontainer-ready-success.svg)

FantasyManager is a **full-stack fantasy football platform**.  
It manages leagues, teams, rosters, and free agents — and is designed to eventually power **trade/signing suggestions** from external stats, projections, and news APIs.

---

## **Table of Contents**

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Clone the Repository](#clone-the-repository)
  - [Open in Devcontainer](#open-in-devcontainer)
  - [Bootstrap the Environment](#bootstrap-the-environment)
  - [Running the Engine (Python API)](#running-the-engine-python-api)
  - [Running the Go Client](#running-the-go-client)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [API](#api)
- [Development Workflow](#development-workflow)
- [Roadmap](#roadmap)
- [Design Notes](#design-notes)
- [Contributing](#contributing)
- [License](#license)

---

## **Features**

### **Currently Implemented**
- Devcontainer environment (Python, Go, Postgres, Redis)
- Python Engine service exposed via HTTP API
- Go client SDK for typed Engine consumption
- PostgreSQL + Redis wired into development environment
- Makefile-based workflow automation (bootstrap, lint, test, codegen)
- Complete OpenAPI spec for the Engine (`engine.openapi.yaml`)

### **Planned / Roadmap**
- League + team management (rosters, lineups, positional structures)
- Free agent pool tracking per league
- Waiver logic (claims, priorities)
- Trade/signing suggestion engine using:
  - Player projections  
  - News/sentiment  
  - Depth chart + positional scarcity  
- First-pass Web UI for owners/managers (Go + HTMX or React)
- Integrations with ESPN/Yahoo/Sleeper APIs
- CI/CD pipelines for automated testing + deployment

---

## **Architecture**

At a high level, FantasyManager looks like this:

```mermaid
flowchart LR
  subgraph Client Layer
    UI[Web UI / CLI]
    GoClient[Go Client SDK]
  end

  subgraph Engine Layer
    API[Engine API (Python)]
    Logic[Domain Logic<br/>valuation, trades, rosters]
  end

  subgraph Data Layer
    DB[(PostgreSQL)]
    Cache[(Redis)]
  end

  UI -->|HTTP/JSON| API
  GoClient -->|HTTP/JSON| API

  API --> Logic
  Logic --> DB
  Logic --> Cache
Engine (Python): domain logic + HTTP API

Go Client: typed client for Go apps/CLIs

Postgres: persistent storage (leagues, teams, players)

Redis: caching + pub/sub + API rate limiting

Tech Stack
Languages
Python 3.13

Go 1.22

Backend
Python Engine (FastAPI-style)

Client SDK
Go client (packages/clients/go)

Data Stores
PostgreSQL

Redis

Tooling
Docker & Docker Compose

VS Code Devcontainers

Makefile automation

OpenAPI spec (engine.openapi.yaml)

Future: GitHub Actions CI/CD

Getting Started
Prerequisites
Docker & Docker Compose

Visual Studio Code with Dev Containers extension

make installed on your system

Clone the Repository
bash
Copy code
git clone https://github.com/kbains09/FantasyManager.git
cd FantasyManager
Open in Devcontainer
Open the folder in VS Code.

Select “Reopen in Container” when prompted.

The devcontainer will automatically install:

Python 3.13

Go 1.22

Postgres & Redis

All dependencies from Poetry & Go modules

Bootstrap the Environment
Inside the devcontainer:

bash
Copy code
make bootstrap
What this does:

Installs Python deps

Installs Go deps

Runs migrations

Starts Postgres + Redis containers

Running the Engine (Python API)
bash
Copy code
make run-engine
Default location:

arduino
Copy code
http://localhost:8000
Health checks:

GET /health/live → {"ok": true}

GET /health/ready → {"ok": true}

Running the Go Client
bash
Copy code
cd packages/clients/go
go run ./cmd/client/main.go
Import path inside Go code:

go
Copy code
import engineapi "github.com/kbains09/FantasyManager/packages/clients/go"
Configuration
Default connection strings (devcontainer):
nginx
Copy code
Postgres → postgresql://dev:dev@localhost:5432/fantasy
Redis    → redis://localhost:6379/0
Override with environment variables:
DATABASE_URL

REDIS_URL

ENGINE_PORT

ENGINE_LOG_LEVEL

TODO: Add docs/CONFIGURATION.md with all options & defaults.

Project Structure
text
Copy code
.devcontainer/          # Devcontainer configs
.vscode/                # Editor recommendations
apis/                   # OpenAPI specs
apps/                   # Future UI / extra services
engine/                 # Python backend (domain logic + API)
infra/                  # Infra-as-code (Docker, Cloud)
migrations/             # Database migrations
packages/
  clients/
    go/                 # Go client SDK + CLI example
Makefile                # Workflow automation
README.md               # Project documentation
API
The Engine API is described using:

bash
Copy code
apis/engine.openapi.yaml
Regenerate the Go client when the API changes:

bash
Copy code
make gen
TODO:

Add /docs + /openapi.json endpoints

Add docs/API.md with detailed examples

Development Workflow
Useful commands
bash
Copy code
make bootstrap     # install deps + initial setup
make run-engine    # run Python Engine API
make run-client    # run Go example client
make lint          # run ruff + go vet + format checks
make test          # run test suites
make gen           # regenerate Go client from OpenAPI
Recommended workflow
Modify OpenAPI (engine.openapi.yaml)

Run make gen to regenerate Go client

Implement/update Python endpoint

Write/update tests

Run make lint test before pushing

Roadmap
Team & League Management
Create/join leagues

Manage rosters and starting lineups

Free Agents & Waivers
Per-league player pools

Waiver claims + rules

Trade & Signing Suggestions
Player value modeling

Depth analysis

Positional scarcity scoring

News + projection data ingestion

Web UI
League dashboard

Team pages

Trade suggestions page

Infrastructure
GitHub Actions CI

Docker image publishing

Cloud Run / GKE deploy pipelines

Design Notes
Goals

Treat fantasy football as a real domain model, not a script collection

Provide a reusable Engine usable from multiple clients

Use OpenAPI-first development to avoid inconsistencies

Key Trade-offs

Python for Engine → flexibility & rich libraries

Go for clients → strongly-typed consumer SDKs

Postgres for relational consistency

Redis for fast ephemeral data

Risks

API rate limits → use caching, retries, backoff

Complex trade logic → enforce modular design + tests

Scope creep → focus on differentiating features

Contributing
Contributions welcome!

Fork the repo

Create a feature branch

bash
Copy code
git checkout -b feature/my-feature
Commit changes

bash
Copy code
git commit -m "Add feature"
Push to your fork

Open a Pull Request

Before submitting, please run:

bash
Copy code
make lint test
License
This project is licensed under the GNU General Public License v3.0 (GPL-3.0).
See the LICENSE file for details.