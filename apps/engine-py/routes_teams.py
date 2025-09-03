from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from services.team_score import compute_team_score
from services.valuation import mock_weekly_projections, compute_vorp_for_week

router = APIRouter()

# --- Mock league (12 teams reduced) ---
_MOCK_TEAMS: Dict[str, Dict[str, Any]] = {
    "t-001": {"id": "t-001", "name": "Kirat FC", "manager": "Kirat"},
    "t-002": {"id": "t-002", "name": "Opponent A", "manager": "Alex"},
}

# roster entries: {player_id, slot}
_MOCK_ROSTERS: Dict[str, List[Dict[str, str]]] = {
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

# minimal player directory (sync with routes_players _MOCK_PLAYERS)
_PLAYER_INDEX: Dict[str, Dict[str, Any]] = {
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

def _build_roster_view(team_id: str, week: int) -> Dict[str, Any]:
    roster = _MOCK_ROSTERS.get(team_id, [])
    # mock league settings: 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX, ignore kickers/DST
    settings = {"roster_rules_json": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1}}
    projections = mock_weekly_projections(_PLAYER_INDEX, week=week, source="mock")
    valuations = compute_vorp_for_week(_PLAYER_INDEX, projections, settings, week)

    roster_items = []
    for slot in roster:
        pid = slot["player_id"]
        player = _PLAYER_INDEX.get(pid)
        val = valuations.get(pid)
        roster_items.append({"player": player, "slot": slot["slot"], "valuation": val})

    team_score = compute_team_score(roster_items, treat_flex_as=("RB", "WR", "TE"))
    return {"roster": roster_items, "team_score": team_score}

@router.get("/teams/{id}")
def get_team(
    id: str,
    week: Optional[int] = Query(None, ge=1, le=18),
):
    team = _MOCK_TEAMS.get(id)
    if not team:
        raise HTTPException(status_code=404, detail="team not found")
    w = week or 1
    view = _build_roster_view(id, w)
    return {"team": team, **view}
