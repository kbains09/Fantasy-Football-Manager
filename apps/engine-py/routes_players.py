"""Player listing endpoints."""
from typing import Optional

from fastapi import APIRouter, Query

from services.mock_data import list_players, paginate

router = APIRouter(tags=["players"])


@router.get("/players")
def get_players(
    pos: Optional[str] = Query(
        None,
        pattern="^(QB|RB|WR|TE|K|DST|FLX)$",
        description="Filter by position",
    ),
    team: Optional[str] = Query(None, description="Filter by NFL team abbreviation"),
    week: Optional[int] = Query(None, ge=1, le=18, description="NFL week (unused currently)"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
) -> dict:
    """
    List players with optional filters.

    Supports filtering by position and NFL team, with cursor-based pagination.
    """
    items = list_players(pos, team)
    page, next_cursor = paginate(items, limit, cursor)
    return {"items": page, "cursor": next_cursor}