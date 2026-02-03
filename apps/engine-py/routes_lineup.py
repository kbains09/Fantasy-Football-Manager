"""Lineup recommendation endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query

from services.mock_data import PLAYERS, SETTINGS, roster, team
from services.projections.registry import get_source
from services.valuation import compute_vorp_for_week

router = APIRouter(tags=["recommend"])

# Positions eligible for FLEX slot
FLEX_POSITIONS = ("RB", "WR", "TE")


# -----------------------------------------------------------------------------
# Lineup Optimization Logic
# -----------------------------------------------------------------------------


def _optimize_lineup(roster_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select optimal starters from a roster based on VORP.

    Uses a greedy algorithm: fills required positions first (QB, RB, WR, TE),
    then selects best remaining FLEX-eligible player.

    Args:
        roster_items: List of roster entries with player, slot, and valuation data

    Returns:
        Dict with starters, bench, and total_vorp
    """
    # Build pool of available players (exclude IR)
    pool: List[Tuple[str, float, Dict[str, Any]]] = []
    for item in roster_items:
        if (item.get("slot") or "").upper() == "IR":
            continue
        pos = (item.get("player") or {}).get("pos")
        vorp = (item.get("valuation") or {}).get("vorp")
        score = float(vorp) if isinstance(vorp, (int, float)) else -999.0
        pool.append((pos, score, item))

    # Sort by VORP descending
    pool.sort(key=lambda x: x[1], reverse=True)

    used_ids: set[str] = set()
    starters: List[Dict[str, Any]] = []

    def take_players(position_filter, slot_label: str, count: int = 1) -> None:
        """Take up to `count` players matching the filter."""
        nonlocal pool
        taken = 0
        i = 0
        while i < len(pool) and taken < count:
            pos, _, item = pool[i]
            player_id = (item.get("player") or {}).get("id")

            if player_id not in used_ids and position_filter(pos):
                starters.append({
                    "slot": slot_label,
                    "player": item["player"],
                    "valuation": item.get("valuation"),
                })
                used_ids.add(player_id)
                pool.pop(i)
                taken += 1
            else:
                i += 1

    # Fill required positions
    take_players(lambda p: p == "QB", "QB", 1)
    take_players(lambda p: p == "RB", "RB", 2)
    take_players(lambda p: p == "WR", "WR", 2)
    take_players(lambda p: p == "TE", "TE", 1)
    take_players(lambda p: p in FLEX_POSITIONS, "FLEX", 1)

    # Remaining players go to bench
    bench = [
        item for _, _, item in pool
        if (item.get("player") or {}).get("id") not in used_ids
    ]

    total_vorp = sum(
        float((s.get("valuation") or {}).get("vorp") or 0.0)
        for s in starters
    )

    return {
        "starters": starters,
        "bench": bench,
        "total_vorp": round(total_vorp, 2),
    }


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.get("/recommend/lineup")
def recommend_lineup(
    team_id: str = Query(..., description="Team ID to optimize lineup for"),
    week: Optional[int] = Query(None, ge=1, le=18, description="NFL week number"),
) -> dict:
    """
    Get optimal lineup recommendation for a team.

    Analyzes the team's roster and returns the highest-VORP starting lineup,
    respecting positional constraints (1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX).
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

    # Build roster view with valuations
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

    # Optimize and return
    result = _optimize_lineup(roster_view)
    result["team"] = team_data
    result["week"] = w
    return result