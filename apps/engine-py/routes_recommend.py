from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services.valuation import compute_vorp_for_week
from services.recommend_fa import recommend_free_agents
from services.recommend_trade import simple_one_for_one_trades
from services.projections.registry import get_source
from services.mock_data import PLAYERS, SETTINGS, team as get_team, roster as get_roster, free_agent_pool, TEAMS

router = APIRouter()

@router.get("/recommend/free-agents")
def recommend_free_agents_route(
    team_id: str = Query(...),
    week: Optional[int] = Query(None, ge=1, le=18),
    limit: int = Query(10, ge=1, le=50),
    cursor: Optional[str] = None,
):
    if not get_team(team_id):
        raise HTTPException(status_code=404, detail="team not found")

    w = week or 1
    src = get_source("mock")
    projections = src.weekly_points(PLAYERS, week=w)
    suggestions = recommend_free_agents(
        players=PLAYERS,
        current_roster=get_roster(team_id),
        free_agents=free_agent_pool(team_id),
        projections=projections,
        settings=SETTINGS,
        week=w,
        top_n=limit,
    )
    return {"items": suggestions, "cursor": None}

class TradeBody(BaseModel):
    team_id: str
    week: Optional[int] = None
    max_offers_per_opponent: int = 2
    aggressiveness: str = "neutral"

@router.post("/recommend/trades")
def recommend_trades_route(body: TradeBody):
    if not get_team(body.team_id):
        raise HTTPException(status_code=404, detail="team not found")
    w = body.week or 1
    src = get_source("mock")
    projections = src.weekly_points(PLAYERS, week=w)
    valuations = compute_vorp_for_week(PLAYERS, projections, SETTINGS, w)

    your = get_roster(body.team_id)
    offers = []
    for opp_id in TEAMS.keys():
        if opp_id == body.team_id:
            continue
        opp_roster = get_roster(opp_id)
        subset = simple_one_for_one_trades(
            players=PLAYERS,
            your_roster=your,
            opp_roster=opp_roster,
            valuations=valuations,
            max_offers=body.max_offers_per_opponent,
        )
        for s in subset:
            s["opponent_team_id"] = opp_id
        offers.extend(subset)

    offers.sort(key=lambda s: s.get("delta_you", 0.0), reverse=True)
    return offers
