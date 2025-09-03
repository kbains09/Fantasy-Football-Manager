# apps/engine-py/seed.py
import os
import time
import json
import requests

ENGINE_BASE_URL = os.environ.get("ENGINE_BASE_URL", "http://localhost:8000")

# --- Mock league payload (matches earlier in-memory mocks) ---
TEAMS = [
    {"id": "t-001", "name": "Kirat FC", "manager": "Kirat"},
    {"id": "t-002", "name": "Opponent A", "manager": "Alex"},
]

ROSTERS = [
    {"team_id": "t-001", "player_id": "QB1", "slot": "QB"},
    {"team_id": "t-001", "player_id": "RB1", "slot": "RB"},
    {"team_id": "t-001", "player_id": "RB2", "slot": "RB"},
    {"team_id": "t-001", "player_id": "WR1", "slot": "WR"},
    {"team_id": "t-001", "player_id": "WR2", "slot": "WR"},
    {"team_id": "t-001", "player_id": "TE1", "slot": "TE"},
    {"team_id": "t-001", "player_id": "RB3", "slot": "BN"},
    {"team_id": "t-001", "player_id": "WR3", "slot": "BN"},
    {"team_id": "t-001", "player_id": "TE2", "slot": "BN"},

    {"team_id": "t-002", "player_id": "QB1", "slot": "QB"},
    {"team_id": "t-002", "player_id": "RB3", "slot": "RB"},
    {"team_id": "t-002", "player_id": "WR3", "slot": "WR"},
    {"team_id": "t-002", "player_id": "TE2", "slot": "TE"},
]

SETTINGS = {
    "scoring_json": {"pass_td": 4, "rush_td": 6},
    "roster_rules_json": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "BN": 6},
    "faab_budget": 200,
}

def _req(method, path, **kwargs):
    url = f"{ENGINE_BASE_URL}{path}"
    r = requests.request(method, url, timeout=15, **kwargs)
    if r.status_code >= 400:
        raise SystemExit(f"{method} {path} -> {r.status_code} {r.text}")
    return r

def main():
    print(f"Seeding against {ENGINE_BASE_URL}")

    # Health
    h = _req("GET", "/v1/health").json()
    print("Health:", h)

    # Ingest league
    payload = {"teams": TEAMS, "rosters": ROSTERS, "settings": SETTINGS}
    _req("POST", "/v1/ingest/league", json=payload)
    print("Ingested league (204)")

    # Trigger valuation compute (mock source)
    job = _req("POST", "/v1/compute/valuations", json={"week": 1, "source": "mock"}).json()
    jid = job["job_id"]
    print("Compute job:", jid)

    # Poll job
    for _ in range(30):
        js = _req("GET", f"/v1/jobs/{jid}").json()
        if js["status"] in ("done", "failed"):
            print("Job status:", js["status"], "| result:", js.get("result_ref"), "| error:", js.get("error"))
            break
        time.sleep(0.2)
    else:
        print("Job still running; moving on.")

    # Demo endpoints
    team = _req("GET", "/v1/teams/t-001", params={"week": 1}).json()
    print("Team view (t-001): team_score =", team.get("team_score"))

    fas = _req("GET", "/v1/recommend/free-agents", params={"team_id": "t-001", "week": 1, "limit": 5}).json()
    print("FA suggestions (top 5):")
    print(json.dumps(fas, indent=2))

    trades = _req("POST", "/v1/recommend/trades", json={"team_id": "t-001", "week": 1}).json()
    print("Trade suggestions:")
    print(json.dumps(trades, indent=2))

if __name__ == "__main__":
    main()
