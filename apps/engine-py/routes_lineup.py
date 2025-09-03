from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services.projections.registry import get_source
from services.valuation import compute_vorp_for_week
from services.team_score import compute_team_score
from services.lineup import recommend_lineup
from services.mock_data import PLAYERS, roster as get_roster, team as get_team, SETTINGS

router = APIRouter()

@router.get("/recommend/lineup")
def recommend_lineup_route(
    team_id: str,
    week: Optional[int] = Query(None, ge=1, le=18),
):
    w = week or 1
    t = get_team(team_id)
    if not t:
        raise HTTPException(status_code=404, detail="team not found")

    src = get_source("mock")
    projections = src.weekly_points(PLAYERS, week=w)
    valuations = compute_vorp_for_week(PLAYERS, projections, SETTINGS, w)

    # build roster view similar to /teams/{id}
    roster = []
    for slot in get_roster(team_id):
        pid = slot["player_id"]
        player = PLAYERS.get(pid)
        val = valuations.get(pid)
        roster.append({"player": player, "slot": slot["slot"], "valuation": val})

    rec = recommend_lineup(roster)
    # optional: team total if you actually applied this lineup
    team_score = compute_team_score(rec["starters"], treat_flex_as=("RB","WR","TE"))
    rec["team_score"] = team_score
    rec["team"] = t
    rec["week"] = w
    return rec
