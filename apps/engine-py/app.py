# apps/engine-py/app.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

app = FastAPI(title="FantasyManager Engine", version="0.1.0")

# ----- Models (mirror OpenAPI) -----
class Team(BaseModel):
    id: str
    name: str
    manager: Optional[str] = None

class Roster(BaseModel):
    team_id: str
    player_id: str
    slot: str 

class LeagueIngest(BaseModel):
    teams: List[Team]
    rosters: List[Roster]
    settings: dict

class FaSuggestion(BaseModel):
    player_id: str
    delta_value: float
    suggested_faab: Optional[int] = None
    rationale: Optional[str] = None

class TradeSuggestion(BaseModel):
    opponent_team_id: str
    give: List[str]
    get: List[str]
    delta_you: float
    delta_them: float
    rationale: Optional[str] = None

# ----- Endpoints -----
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest/league", status_code=204)
def ingest_league(payload: LeagueIngest):
    # TODO: persist teams, rosters, settings -> DB
    # For now, just accept and return 204
    return

@app.post("/compute/valuations", status_code=202)
def compute_valuations(week: Optional[int] = None, source: Optional[str] = None):
    # TODO: enqueue a job / run valuation computation
    # For now, pretend we started a job
    return

@app.get("/recommend/free-agents", response_model=List[FaSuggestion])
def recommend_free_agents(
    team_id: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
):
    # TODO: implement with real valuations + roster needs
    sample = [
        FaSuggestion(player_id="wr_keenan_allen", delta_value=12.4, suggested_faab=18, rationale="WR2 upgrade"),
        FaSuggestion(player_id="rb_jaylen_warren", delta_value=8.7, suggested_faab=12, rationale="RB depth + pass game"),
        FaSuggestion(player_id="te_sam_laporta", delta_value=7.9, suggested_faab=10, rationale="Big red-zone role"),
    ]
    return sample[:limit]

@app.post("/recommend/trades", response_model=List[TradeSuggestion])
def recommend_trades(
    body: dict
):
    # Basic validation
    team_id = body.get("team_id")
    if not team_id:
        raise HTTPException(status_code=400, detail="team_id is required")

    # TODO: implement trade search with constraints
    sample = [
        TradeSuggestion(
            opponent_team_id="team_b",
            give=["rb_your_rb2"],
            get=["wr_their_wr2"],
            delta_you=9.3,
            delta_them=1.2,
            rationale="You’re WR‑needy; they’re RB‑needy",
        )
    ]
    return sample
