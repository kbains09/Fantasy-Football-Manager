"""Team roster and valuation endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.mock_data import PLAYERS, SETTINGS, roster, team
from services.projections.registry import get_source
from services.valuation import compute_vorp_for_week

router = APIRouter(tags=["teams"])


@router.get("/teams/{team_id}")
def get_team(
    team_id: str,
    week: Optional[int] = Query(None, ge=1, le=18, description="NFL week number"),
) -> dict:
    """
    Get team details with full roster and valuations.

    Returns the team info, roster with player details and VORP valuations,
    and total team score.
    """
    w = week or 1

    # Validate team exists
    team_data = team(team_id)
    if not team_data:
        raise HTTPException(status_code=404, detail="Team not found")

    # Compute valuations for the week
    src = get_source("mock")
    projections = src.weekly_points(PLAYERS, week=w)
    valuations = compute_vorp_for_week(PLAYERS, projections, SETTINGS, w)

    # Build roster view
    roster_view = []
    for slot in roster(team_id):
        player_id = slot["player_id"]
        player = PLAYERS.get(player_id)
        valuation = valuations.get(player_id)
        roster_view.append({
            "player": player,
            "slot": slot["slot"],
            "valuation": valuation,
        })

    # Calculate total team VORP
    team_score = sum(
        float((r.get("valuation") or {}).get("vorp") or 0.0)
        for r in roster_view
    )

    return {
        "team": team_data,
        "roster": roster_view,
        "team_score": round(team_score, 2),
    }