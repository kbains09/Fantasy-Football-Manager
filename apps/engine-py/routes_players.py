from fastapi import APIRouter, Query
from typing import Optional
from services.mock_data import list_players, paginate

router = APIRouter()

@router.get("/players")
def list_players_route(
    pos: Optional[str] = Query(None, pattern="^(QB|RB|WR|TE|K|DST|FLX)$"),
    team: Optional[str] = None,
    week: Optional[int] = Query(None, ge=1, le=18),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = None,
):
    items = list_players(pos, team)
    page, next_cursor = paginate(items, limit, cursor)
    return {"items": page, "cursor": next_cursor}
