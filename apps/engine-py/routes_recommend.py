from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from services.valuation import mock_weekly_projections, compute_vorp_for_week
from services.recommend_fa import recommend_free_agents
from services.recommend_trade import simple_one_for_one_trades

router = APIRouter()

# --- Minimal shared mocks (keep in sync with routes_players / routes_teams) ---
_PLAYERS: Dict[str, Dict[str, Any]] = {
    "QB1": {"id": "QB1", "name": "Quentin Ball", "pos": "QB", "team": "BUF"},
    "RB1": {"id": "RB1", "name": "Ricky Burst", "pos": "RB", "team": "SF"},
    "RB2": {"id": "RB2", "name": "Randy Breaker", "pos": "RB", "team": "KC"},
    "WR1": {"id": "WR1", "name": "Walt Rocket", "pos": "WR", "team": "DAL"},
    "WR2": {"id": "WR2", "name": "Wes Runner", "pos": "WR", "team": "MIA"},
    "TE1": {"id": "TE1", "name": "Terry Edge", "pos": "TE", "team": "KC"},
    "RB3": {"id": "RB3", "name": "Rico Backup", "pos": "RB", "team": "JAX"},
    "WR3": {"id": "WR3", "name": "Wade Slot", "pos": "WR", "team": "NYJ"},
    "TE2": {"id": "TE2", "name": "Tony Blocker", "pos": "TE", "team": "LAR"},
}

_TEAMS: Dict[str, Dict[str, Any]] = {
    "t-001": {"id": "t-001", "name": "Kirat FC", "manager": "Kirat"},
    "t-002": {"id": "t-002", "name": "Opponent A", "manager": "Alex"},
}

_ROSTERS: Dict[str, List[Dict[str, str]]] = {
    "t-001": [
        {"player_id": "QB1", "slot": "QB"},
        {"player_id": "RB1", "slot": "RB"},
        {"player_id": "RB2", "slot": "RB"},
        {"player_id": "WR1", "slot": "WR"},
        {"player_id": "WR2", "slot": "WR"},
        {"player_id": "TE1", "slot": "TE"},
        {"player_id": "RB3", "slot": "BN"},
        {"player_id": "WR3", "slot": "BN"},
        {"player_id": "TE2", "slot": "BN"},
    ],
    "t-002": [
        {"player_id": "QB1", "slot": "QB"},
        {"player_id": "RB3", "slot": "RB"},
        {"player_id": "WR3", "slot": "WR"},
        {"player_id": "TE2", "slot": "TE"},
    ],
}

_SETTINGS = {"roster_rules_json": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1}}

# ---------- Free Agents ----------
@router.get("/recommend/free-agents")
def recommend_free_agents_route(
    team_id: str = Query(...),
    week: Optional[int] = Query(None, ge=1, le=18),
    limit: int = Query(10, ge=1, le=50),
    cursor: Optional[str] = None,   # cursor is ignored in mock
):
    if team_id not in _TEAMS:
        raise HTTPException(status_code=404, detail="team not found")

    w = week or 1
    # fake free agent pool = players not on your active roster
    your_pids = {r["player_id"] for r in _ROSTERS.get(team_id, [])}
    fa_pool = [pid for pid in _PLAYERS.keys() if pid not in your_pids]

    projections = mock_weekly_projections(_PLAYERS, week=w, source="mock")
    suggestions = recommend_free_agents(
        players=_PLAYERS,
        current_roster=_ROSTERS.get(team_id, []),
        free_agents=fa_pool,
        projections=projections,
        settings=_SETTINGS,
        week=w,
        top_n=limit,
    )
    # wrap as a paged object to match spec
    return {"items": suggestions, "cursor": None}

# ---------- Trades ----------
class TradeBody(BaseModel):
    team_id: str
    week: Optional[int] = None
    max_offers_per_opponent: int = 2
    aggressiveness: str = "neutral"

@router.post("/recommend/trades")
def recommend_trades_route(body: TradeBody):
    team_id = body.team_id
    if team_id not in _TEAMS:
        raise HTTPException(status_code=404, detail="team not found")
    w = body.week or 1

    projections = mock_weekly_projections(_PLAYERS, week=w, source="mock")
    valuations = compute_vorp_for_week(_PLAYERS, projections, _SETTINGS, w)

    your = _ROSTERS.get(team_id, [])
    offers = []
    for opp_id, opp in _TEAMS.items():
        if opp_id == team_id:
            continue
        opp_roster = _ROSTERS.get(opp_id, [])
        subset = simple_one_for_one_trades(
            players=_PLAYERS,
            your_roster=your,
            opp_roster=opp_roster,
            valuations=valuations,
            max_offers=body.max_offers_per_opponent,
        )
        # fill opponent id into suggestion
        for s in subset:
            s["opponent_team_id"] = opp_id
        offers.extend(subset)

    # naive sort by your gain desc
    offers.sort(key=lambda s: s.get("delta_you", 0.0), reverse=True)
    return offers
