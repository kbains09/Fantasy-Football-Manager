# Single source of truth for in-memory data (temp until Postgres).
from __future__ import annotations
from typing import Dict, Any, List, Optional

# Core collections
PLAYERS: Dict[str, Dict[str, Any]] = {}
TEAMS: Dict[str, Dict[str, Any]] = {}
ROSTERS: Dict[str, List[Dict[str, str]]] = {}  # team_id -> [{player_id, slot}]
SETTINGS: Dict[str, Any] = {
    "scoring_json": {"pass_td": 4, "rush_td": 6},
    "roster_rules_json": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "BN": 6},
    "faab_budget": 200,
}

def team(team_id: str) -> Optional[Dict[str, Any]]:
    return TEAMS.get(team_id)

def roster(team_id: str) -> List[Dict[str, str]]:
    return list(ROSTERS.get(team_id, []))

def reset() -> None:
    PLAYERS.clear()
    TEAMS.clear()
    ROSTERS.clear()
