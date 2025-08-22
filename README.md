# FantasyManager

**FantasyManager** is a full-stack project for managing fantasy football leagues. It allows you to manage teams, free agents, and generate trade/signing suggestions using outside APIs for news and stats.

The project uses:

* **Python backend (Engine)** – Core API & business logic
* **Go client** – Example service client for interacting with the Engine
* **PostgreSQL** – Persistent storage
* **Redis** – Caching & pub/sub
* **Devcontainers + Docker** – Standardized local development environment

---

## 🚀 Quick Start

### 1. Prerequisites

* [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
* [Visual Studio Code](https://code.visualstudio.com/) with **Dev Containers** extension
* Make (for running commands)

---

### 2. Clone the Repository

```bash
git clone https://github.com/kbains09/FantasyManager.git
cd FantasyManager
```

---

### 3. Open in Devcontainer

1. Open the repo in **VS Code**
2. When prompted, “Reopen in Container” (or run `Dev Containers: Reopen in Container` from Command Palette).
3. This will build and start a container with:

   * Python 3.13
   * Go 1.22
   * Postgres & Redis services
   * All dependencies from `pyproject.toml` / `go.mod`

---

### 4. Bootstrap the Environment

Run inside the devcontainer:

```bash
make bootstrap
```

This will:

* Install Python deps
* Install Go deps
* Run DB migrations
* Start local services

---

### 5. Running the Backend (Engine)

Start the Python API server:

```bash
make run-engine
```

By default, it runs at:

```
http://localhost:8000
```

Health checks:

* `GET /health/live` → `{"ok": true}`
* `GET /health/ready` → `{"ok": true}`

---

### 6. Running the Go Client

Build and run the Go client:

```bash
cd packages/clients/go
go run ./cmd/client/main.go
```

The client talks to the Engine using the module import path:

```go
import engineapi "github.com/kbains09/FantasyManager/packages/clients/go"
```

---

### 7. Database & Caching

Postgres and Redis are started as part of the devcontainer.
Default connection strings:

```
Postgres → postgresql://dev:dev@localhost:5432/fantasy
Redis    → redis://localhost:6379/0
```

---

## 📂 Project Structure

```
.devcontainer/        # Dev container configs
packages/
  clients/go/         # Go client for Engine API
engine/               # Python backend (FastAPI or similar)
migrations/           # Database migrations
Makefile              # Common commands
```

---

## 🛠 Common Commands

```bash
make bootstrap     # install deps, run setup
make run-engine    # start Python backend
make run-client    # run Go client
make lint          # run linters (ruff, go vet, etc.)
make test          # run all tests
```

---

## 📝 API

The Engine API is described in **`engine.openapi.yaml`**.
To regenerate the Go client after updating the spec:

```bash
make gen
```

---

## 🔮 Roadmap

* [ ] Team management
* [ ] Free agent pool tracking
* [ ] Trade & signing suggestions (stats/news APIs)
* [ ] Web UI

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/my-feature`)
5. Open a PR

---

## 📜 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).
See the LICENSE file for details.
---