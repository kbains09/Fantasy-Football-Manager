# FantasyManager – Configuration Guide

This document explains all environment variables and configuration options used by FantasyManager.

---

## 1. Overview

FantasyManager is configured through environment variables, making it portable across local development, devcontainers, and cloud deployments.

**Current Architecture:**
- Python Engine (FastAPI) — core domain logic + HTTP API
- Go Client SDK — generated from OpenAPI spec
- PostgreSQL — database models defined (optional for demo mode)
- In-memory store — default for zero-setup demos

---

## 2. Environment Variables

### Implemented & Working

These variables are actively used by the codebase.

#### ESPN Integration

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `ESPN_LEAGUE_ID` | Your ESPN fantasy league ID | Yes (for ESPN sync) | `12345678` |
| `ESPN_YEAR` | Season year | Yes (for ESPN sync) | `2024` |
| `ESPN_S2` | ESPN authentication cookie | Private leagues only | `AEC...long string` |
| `ESPN_SWID` | ESPN user identifier (GUID with braces) | Private leagues only | `{XXXXXXXX-XXXX-...}` |
| `ESPN_MY_TEAM_ID` | Manual override for your team ID | Optional | `espn-5` |

**How to get ESPN cookies (for private leagues):**
1. Log into ESPN Fantasy in your browser
2. Open Developer Tools → Application → Cookies
3. Find `espn_s2` and `SWID` cookies
4. Copy values to your `.env` file

#### Database (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_URL` | PostgreSQL connection string | Uses in-memory mock data if not set |

**Format:** `postgresql+psycopg://user:password@host:port/database`

**Devcontainer default:** `postgresql+psycopg://dev:dev@postgres:5432/fantasy`

> **Note:** The current API routes use in-memory mock data by default. Database models are defined in `apps/engine-py/db/models.py` but not yet wired to routes. ESPN sync populates the in-memory store.

---

### Planned (Not Yet Implemented)

These variables are documented for future development but have no effect currently.

| Variable | Intended Purpose | Status |
|----------|------------------|--------|
| `REDIS_URL` | Redis connection for caching | In devcontainer stack, not used in code |
| `ENGINE_PORT` | Override default port | Hardcoded to 8000 |
| `ENGINE_LOG_LEVEL` | Log verbosity (debug/info/warning/error) | Not implemented |
| `ENGINE_WORKERS` | Uvicorn worker count | Not implemented |
| `ENABLE_CACHE` | Toggle Redis caching | Not implemented |
| `CACHE_TTL_SECONDS` | Cache TTL for projections | Not implemented |
| `ENABLE_RATE_LIMITING` | Throttle external API calls | Not implemented |
| `RATE_LIMIT_CALLS_PER_MINUTE` | Rate limit threshold | Not implemented |
| `EXTERNAL_API_KEY_FFPROS` | FantasyPros API key | Not implemented |
| `EXTERNAL_API_KEY_NEWS_API` | News API key | Not implemented |

---

## 3. Environment Files

### Local Development (`.env`)

Create `apps/engine-py/.env` for local configuration:

```env
# ESPN Integration (required for real league data)
ESPN_LEAGUE_ID=12345678
ESPN_YEAR=2024
ESPN_S2=your_espn_s2_cookie_here
ESPN_SWID={YOUR-SWID-GUID-HERE}

# Optional: Manual team ID override
# ESPN_MY_TEAM_ID=espn-5

# Optional: Database (omit to use in-memory mock data)
# DB_URL=postgresql+psycopg://dev:dev@postgres:5432/fantasy
```

This file is gitignored and loaded automatically by the devcontainer.

### Production Example (`.env.prod`)

```env
# Database (required for production)
DB_URL=postgresql+psycopg://user:password@prod-db:5432/fantasy

# ESPN (if using ESPN sync in production)
ESPN_LEAGUE_ID=12345678
ESPN_YEAR=2024
ESPN_S2=${ESPN_S2_SECRET}
ESPN_SWID=${ESPN_SWID_SECRET}
```

---

## 4. Configuration by Environment

### Devcontainer (Recommended for Development)

The devcontainer automatically provides:
- Python 3.13 with Poetry
- Go 1.22
- PostgreSQL at `postgres:5432`
- Redis at `redis:6379` (available but unused)

Default environment variables are set in `.devcontainer/devcontainer.json`:

```json
{
  "remoteEnv": {
    "ENGINE_BASE_URL": "http://app:8000",
    "DB_URL": "postgresql://dev:dev@postgres:5432/fantasy"
  }
}
```

### Docker Compose (Production-like)

Using `infra/compose.yaml`:

```bash
# Start all services
docker compose -f infra/compose.yaml up -d

# View logs
docker compose -f infra/compose.yaml logs -f
```

Environment variables can be overridden:

```yaml
services:
  engine:
    environment:
      DB_URL: postgresql+psycopg://dev:dev@db:5432/fantasy
      ESPN_LEAGUE_ID: "12345678"
      ESPN_YEAR: "2024"
```

### Cloud Run / GKE (Future)

```bash
gcloud run deploy fantasy-engine \
  --image gcr.io/project/fantasy-engine \
  --set-env-vars DB_URL=$DATABASE_URL \
  --set-env-vars ESPN_LEAGUE_ID=$ESPN_LEAGUE_ID \
  --set-env-vars ESPN_YEAR=$ESPN_YEAR \
  --set-secrets ESPN_S2=espn-s2:latest,ESPN_SWID=espn-swid:latest
```

---

## 5. Debugging Configuration Issues

### "ESPN sync returns 401 or empty data"

- **Private league?** You need both `ESPN_S2` and `ESPN_SWID` cookies
- **Cookies expired?** Re-copy from browser (they expire periodically)
- **Wrong league ID?** Check the URL when viewing your league on ESPN

### "Cannot detect my team"

The `/v1/me/team` endpoint tries to match your `ESPN_SWID` to team owners. If it fails:
1. Use `/v1/sync/espn/check` to see all teams and their owner IDs
2. Set `ESPN_MY_TEAM_ID=espn-X` manually in your `.env`

### "Database connection refused"

- Ensure Postgres is running: `docker ps | grep postgres`
- Check connection string format includes `+psycopg` driver
- Verify port 5432 is accessible

### "Environment variables not loading"

- Ensure `.env` is in `apps/engine-py/` (not project root)
- Restart the devcontainer after changes
- Check for typos in variable names

---

## 6. Configuration Validation

On startup, the Engine logs which configuration is active. Check the console output:

```
INFO:     ESPN_LEAGUE_ID: 12345678
INFO:     ESPN_YEAR: 2024
INFO:     ESPN cookies: configured
INFO:     Database: using in-memory mock data
```

You can also verify ESPN configuration via API:

```bash
curl http://localhost:8000/v1/sync/espn/check
```

---

## 7. Document History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2024-11-23 | Initial configuration document |
| 1.1 | 2025-02-02 | Updated to reflect implemented vs planned features |