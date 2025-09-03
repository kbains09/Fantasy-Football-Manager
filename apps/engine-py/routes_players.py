from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any

router = APIRouter()

# --- Mock catalog (replace with DB later) ---
_MOCK_PLAYERS: List[Dict[str, Any]] = [
    {"id": "QB1", "ext_id": "E_QB1", "name": "Quentin Ball", "pos": "QB", "team": "BUF", "bye_week": 13, "status": "ACT"},
    {"id": "RB1", "ext_id": "E_RB1", "name": "Ricky Burst", "pos": "RB", "team": "SF",  "bye_week": 9,  "status": "ACT"},
    {"id": "RB2", "ext_id": "E_RB2", "name": "Randy Breaker", "pos": "RB", "team": "KC",  "bye_week": 10, "status": "ACT"},
    {"id": "WR1", "ext_id": "E_WR1", "name": "Walt Rocket", "pos": "WR", "team": "DAL", "bye_week": 7,  "status": "ACT"},
    {"id": "WR2", "ext_id": "E_WR2", "name": "Wes Runner", "pos": "WR", "team": "MIA", "bye_week": 6,  "status": "ACT"},
    {"id": "TE1", "ext_id": "E_TE1", "name": "Terry Edge", "pos": "TE", "team": "KC",  "bye_week": 10, "status": "ACT"},
    {"id": "RB3", "ext_id": "E_RB3", "name": "Rico Backup", "pos": "RB", "team": "JAX", "bye_week": 12, "status": "ACT"},
    {"id": "WR3", "ext_id": "E_WR3", "name": "Wade Slot", "pos": "WR", "team": "NYJ", "bye_week": 12, "status": "ACT"},
    {"id": "TE2", "ext_id": "E_TE2", "name": "Tony Blocker", "pos": "TE", "team": "LAR","bye_week": 11, "status": "ACT"},
]

def _filter_players(pos: Optional[str], nfl_team: Optional[str]) -> List[Dict[str, Any]]:
    items = _MOCK_PLAYERS
    if pos:
        items = [p for p in items if p["pos"] == pos]
    if nfl_team:
        items = [p for p in items if p["team"] == nfl_team]
    return items

def _apply_cursor(items: List[Dict[str, Any]], limit: int, cursor: Optional[str]):
    # simple offset cursor: cursor = str(offset)
    try:
        offset = int(cursor) if cursor is not None else 0
    except ValueError:
        offset = 0
    slice_ = items[offset: offset + limit]
    next_cursor = str(offset + limit) if offset + limit < len(items) else None
    return slice_, next_cursor

@router.get("/players")
def list_players(
    pos: Optional[str] = Query(None, pattern="^(QB|RB|WR|TE|K|DST|FLX)$"),
    team: Optional[str] = None,
    week: Optional[int] = Query(None, ge=1, le=18),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = None,
):
    # week is unused in this mock; kept for contract compatibility
    items = _filter_players(pos, team)
    page, next_cursor = _apply_cursor(items, limit, cursor)
    return {"items": page, "cursor": next_cursor}
