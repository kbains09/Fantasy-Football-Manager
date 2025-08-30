from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Player, Roster, Team, Valuation

app = FastAPI(title="FantasyManager Engine", version="0.1.0")


# ---------- Pydantic I/O models ----------
class TeamIn(BaseModel):
    id: str
    name: str
    manager: Optional[str] = None


class RosterIn(BaseModel):
    team_id: str
    player_id: str
    slot: str


class LeagueIngest(BaseModel):
    teams: List[TeamIn]
    rosters: List[RosterIn]
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


# ---------- DB session dependency ----------
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Routes ----------
@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ingest/league", status_code=204)
def ingest_league(payload: LeagueIngest, db: Session = Depends(get_db)):
    """
    MVP upsert for teams + full replace of rosters for the given payload.
    Players referenced in rosters are auto-created if missing (pos=None).
    """
    # upsert teams
    for t in payload.teams:
        existing = db.get(Team, t.id)
        if existing:
            existing.name = t.name
            existing.manager = t.manager
        else:
            db.add(Team(id=t.id, name=t.name, manager=t.manager))

    # full replace rosters (simple strategy for now)
    db.execute(delete(Roster))
    for r in payload.rosters:
        if not db.get(Player, r.player_id):
            db.add(Player(id=r.player_id, pos=None))
        db.add(Roster(team_id=r.team_id, player_id=r.player_id, slot=r.slot))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Integrity error during ingest")


@app.post("/compute/valuations", status_code=202)
def compute_valuations(
    week: int | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Naive baseline: assign a fixed value by position so we can exercise the UI end-to-end.
    Re-runs overwrite the same (source, week).
    """
    pos_weight = {"RB": 12.0, "WR": 11.0, "QB": 10.0, "TE": 8.0, None: 6.0}
    w = week or 0
    s = source or "baseline"

    players = db.execute(select(Player)).scalars().all()
    db.execute(delete(Valuation).where(Valuation.source == s, Valuation.week == w))
    for p in players:
        val = pos_weight.get(p.pos, 6.0)
        db.add(Valuation(player_id=p.id, value=val, source=s, week=w))

    db.commit()


@app.get("/recommend/free-agents", response_model=List[FaSuggestion])
def recommend_free_agents(
    team_id: str = Query(...),
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    “Free agents” = players not on any roster.
    Rank by valuation delta vs the requesting team’s average valuation.
    """
    # rostered ids (all) + this team's ids
    rostered_ids = {
        r.player_id for r in db.execute(select(Roster)).scalars().all()
    }
    my_ids = {
        r.player_id
        for r in db.execute(select(Roster).where(Roster.team_id == team_id)).scalars().all()
    }

    # valuation map
    vals_map = {
        v.player_id: v.value for v in db.execute(select(Valuation)).scalars().all()
    }

    # team average
    my_vals = [vals_map.get(pid, 0.0) for pid in my_ids]
    my_avg = sum(my_vals) / len(my_vals) if my_vals else 0.0

    # only players with a valuation and not rostered
    fa_ids = [pid for pid in vals_map.keys() if pid not in rostered_ids]

    suggestions: list[FaSuggestion] = []
    for pid in fa_ids:
        v = float(vals_map.get(pid, 0.0))
        delta = v - my_avg
        suggestions.append(
            FaSuggestion(
                player_id=pid,
                delta_value=round(delta, 2),
                suggested_faab=max(0, int(v // 2)),
                rationale="Baseline valuation vs your avg",
            )
        )

    suggestions.sort(key=lambda x: x.delta_value, reverse=True)
    return suggestions[:limit]
