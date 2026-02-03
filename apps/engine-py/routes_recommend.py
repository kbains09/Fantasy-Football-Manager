"""Recommendation endpoints for free agents and trades."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.mock_data import (
    PLAYERS,
    SETTINGS,
    TEAMS,
    free_agent_pool,
    roster as get_roster,
    team as get_team,
)
from services.projections.registry import get_source
from services.recommend_fa import recommend_free_agents
from services.recommend_trade import simple_one_for_one_trades
from services.valuation import compute_vorp_for_week

router = APIRouter(tags=["recommend"])


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------


class TradeRequest(BaseModel):
    """Request body for trade recommendations."""

    team_id: str = Field(description="Your team ID")
    week: Optional[int] = Field(None, ge=1, le=18, description="NFL week number")
    max_offers_per_opponent: int = Field(
        default=2, ge=1, le=10, description="Max trade offers to generate per opponent"
    )
    aggressiveness: str = Field(
        default="neutral",
        description="Trade aggressiveness: conservative, neutral, or aggressive",
    )


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.get("/recommend/free-agents")
def get_free_agent_recommendations(
    team_id: str = Query(..., description="Your team ID"),
    week: Optional[int] = Query(None, ge=1, le=18, description="NFL week number"),
    limit: int = Query(10, ge=1, le=50, description="Max suggestions to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (unused)"),
) -> dict:
    """
    Get ranked free agent pickup suggestions.

    Returns players not on any roster, ranked by how much they would
    improve your team's total VORP compared to your current weakest players.
    """
    if not get_team(team_id):
        raise HTTPException(status_code=404, detail="Team not found")

    w = week or 1

    # Compute projections and valuations
    src = get_source("mock")
    projections = src.weekly_points(PLAYERS, week=w)

    # Get recommendations
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


@router.post("/recommend/trades")
def get_trade_recommendations(body: TradeRequest) -> List[dict]:
    """
    Get trade suggestions that improve your team.

    Analyzes all opponents' rosters and suggests 1-for-1 trades where:
    - You gain VORP (your team improves)
    - The trade is roughly fair (opponent doesn't lose significantly)

    Results are sorted by your VORP gain (best trades first).
    """
    if not get_team(body.team_id):
        raise HTTPException(status_code=404, detail="Team not found")

    w = body.week or 1

    # Compute projections and valuations
    src = get_source("mock")
    projections = src.weekly_points(PLAYERS, week=w)
    valuations = compute_vorp_for_week(PLAYERS, projections, SETTINGS, w)

    # Get your roster
    your_roster = get_roster(body.team_id)

    # Generate trade offers against each opponent
    all_offers: List[dict] = []
    for opponent_id in TEAMS.keys():
        if opponent_id == body.team_id:
            continue

        opponent_roster = get_roster(opponent_id)
        offers = simple_one_for_one_trades(
            players=PLAYERS,
            your_roster=your_roster,
            opp_roster=opponent_roster,
            valuations=valuations,
            max_offers=body.max_offers_per_opponent,
        )

        # Tag each offer with the opponent
        for offer in offers:
            offer["opponent_team_id"] = opponent_id
        all_offers.extend(offers)

    # Sort by your gain (best trades first)
    all_offers.sort(key=lambda x: x.get("delta_you", 0.0), reverse=True)

    return all_offers