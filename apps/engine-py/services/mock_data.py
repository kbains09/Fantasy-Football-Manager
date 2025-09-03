from __future__ import annotations
from typing import Dict, Any, List, Optional

# --- Expanded mock player pool (20 players across positions) ---
PLAYERS: Dict[str, Dict[str, Any]] = {
    "QB1": {"id": "QB1", "name": "Quentin Ball", "pos": "QB", "team": "BUF"},
    "QB2": {"id": "QB2", "name": "Kyle Laser",   "pos": "QB", "team": "LAC"},
    "RB1": {"id": "RB1", "name": "Ricky Burst",  "pos": "RB", "team": "SF"},
    "RB2": {"id": "RB2", "name": "Randy Breaker","pos": "RB", "team": "KC"},
    "RB3": {"id": "RB3", "name": "Rico Backup",  "pos": "RB", "team": "JAX"},
    "RB4": {"id": "RB4", "name": "Ronan Cutter", "pos": "RB", "team": "DET"},
    "WR1": {"id": "WR1", "name": "Walt Rocket",  "pos": "WR", "team": "DAL"},
    "WR2": {"id": "WR2", "name": "Wes Runner",   "pos": "WR", "team": "MIA"},
    "WR3": {"id": "WR3", "name": "Wade Slot",    "pos": "WR", "team": "NYJ"},
    "WR4": {"id": "WR4", "name": "Wayne Streak", "pos": "WR", "team": "SEA"},
    "WR5": {"id": "WR5", "name": "Will Zippy",   "pos": "WR", "team": "CIN"},
    "TE1": {"id": "TE1", "name": "Terry Edge",   "pos": "TE", "team": "KC"},
    "TE2": {"id": "TE2", "name": "Tony Blocker", "pos": "TE", "team": "LAR"},
    "TE3": {"id": "TE3", "name": "Toby Chip",    "pos": "TE", "team": "MIN"},
    "K1":  {"id": "K1",  "name": "Ken Boots",    "pos": "K",  "team": "BAL"},
    "K2":  {"id": "K2",  "name": "Kurt Aim",     "pos": "K",  "team": "DAL"},
    "D1":  {"id": "D1",  "name": "Niners D/ST",  "pos": "DST","team": "SF"},
    "D2":  {"id": "D2",  "name": "Jets D/ST",    "pos": "DST","team": "NYJ"},
    "RB5": {"id": "RB5", "name": "Robbie Burst", "pos": "RB", "team": "BUF"},
    "WR6": {"id": "WR6", "name": "Wiley Deep",   "pos": "WR", "team": "JAX"},
}

TEAMS: Dict[str, Dict[str, Any]] = {
    "t-001": {"id": "t-001", "name": "Kirat FC", "manager": "Kirat"},
    "t-002": {"id": "t-002", "name": "Opponent A", "manager": "Alex"},
}

# Your roster is a reasonable set (doesn't cover entire pool)
ROSTERS: Dict[str, List[Dict[str, str]]] = {
    "t-001": [
        {"player_id": "QB1", "slot": "QB"},
        {"player_id": "RB1", "slot": "RB"},
        {"player_id": "RB2", "slot": "RB"},
        {"player_id": "WR1", "slot": "WR"},
        {"player_id": "WR2", "slot": "WR"},
        {"player_id": "TE1", "slot": "TE"},
        {"player_id": "RB3", "slot": "BN"},
        {"player_id": "WR3", "slot": "BN"},
        {"player_id": "TE2", "slot": "BN"},
    ],
    "t-002": [
        {"player_id": "QB2", "slot": "QB"},
        {"player_id": "RB4", "slot": "RB"},
        {"player_id": "WR4", "slot": "WR"},
        {"player_id": "TE3", "slot": "TE"},
    ],
}

SETTINGS = {"roster_rules_json": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "BN": 6}}

# ----------------- Helpers used by routes -----------------
def list_players(pos: Optional[str] = None, nfl_team: Optional[str] = None) -> List[Dict[str, Any]]:
    items = list(PLAYERS.values())
    if pos:
        items = [p for p in items if p["pos"] == pos]
    if nfl_team:
        items = [p for p in items if p["team"] == nfl_team]
    return items

def paginate(items: List[Dict[str, Any]], limit: int, cursor: Optional[str]):
    try:
        offset = int(cursor) if cursor is not None else 0
    except ValueError:
        offset = 0
    slice_ = items[offset: offset + limit]
    next_cursor = str(offset + limit) if offset + limit < len(items) else None
    return slice_, next_cursor

def team(team_id: str) -> Optional[Dict[str, Any]]:
    return TEAMS.get(team_id)

def roster(team_id: str) -> List[Dict[str, str]]:
    return ROSTERS.get(team_id, [])

def free_agent_pool(team_id: str) -> List[str]:
    on_team = {r["player_id"] for r in roster(team_id)}
    return [pid for pid in PLAYERS.keys() if pid not in on_team]
