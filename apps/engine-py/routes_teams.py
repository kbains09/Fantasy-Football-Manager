from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from services.team_score import compute_team_score
from services.valuation import compute_vorp_for_week
from services.projections.registry import get_source
from services.mock_data import PLAYERS, team as get_team, roster as get_roster, SETTINGS

router = APIRouter()

def _build_roster_view(team_id: str, week: int) -> Dict[str, Any]:
    roster = get_roster(team_id)
    src = get_source("mock")
    projections = src.weekly_points(PLAYERS, week=week)
    valuations = compute_vorp_for_week(PLAYERS, projections, SETTINGS, week)

    roster_items = []
    for slot in roster:
        pid = slot["player_id"]
        player = PLAYERS.get(pid)
        val = valuations.get(pid)
        roster_items.append({"player": player, "slot": slot["slot"], "valuation": val})

    team_score = compute_team_score(roster_items, treat_flex_as=("RB", "WR", "TE"))
    return {"roster": roster_items, "team_score": team_score}

@router.get("/teams/{id}")
def get_team_route(
    id: str,
    week: Optional[int] = Query(None, ge=1, le=18),
):
    t = get_team(id)
    if not t:
        raise HTTPException(status_code=404, detail="team not found")
    w = week or 1
    view = _build_roster_view(id, w)
    return {"team": t, **view}
