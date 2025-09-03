from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services import store  # << use canonical store
from services.projections.registry import get_source
from services.valuation import compute_vorp_for_week

router = APIRouter()

@router.get("/teams/{id}", summary="Get Team Route")
def get_team_route(id: str, week: Optional[int] = Query(None, ge=1, le=18)):
    w = week or 1
    t = store.team(id)
    if not t:
        raise HTTPException(status_code=404, detail="team not found")

    src = get_source("mock")
    projections = src.weekly_points(store.PLAYERS, week=w)
    valuations = compute_vorp_for_week(store.PLAYERS, projections, store.SETTINGS, w)

    roster = []
    for slot in store.roster(id):
        pid = slot["player_id"]
        player = store.PLAYERS.get(pid)
        val = valuations.get(pid)
        roster.append({"player": player, "slot": slot["slot"], "valuation": val})

    # team_score example if you have a helper:
    team_score = sum(float((r.get("valuation") or {}).get("vorp") or 0.0) for r in roster)
    return {"team": t, "roster": roster, "team_score": round(team_score, 2)}
