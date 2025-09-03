# apps/engine-py/adapters/espn/sync.py
from __future__ import annotations
from typing import Dict, Any
from .client import ESPNClient
from services import mock_data as store

def full_sync() -> Dict[str, Any]:
    c = ESPNClient()

    # Teams
    store.TEAMS.clear()
    for t in c.teams():
        store.TEAMS[t["id"]] = t

    # Rosters
    store.ROSTERS.clear()
    for r in c.rosters():
        store.ROSTERS.setdefault(r["team_id"], []).append({
            "player_id": r["player_id"],
            "slot": r["slot"],
        })

    # Settings
    store.SETTINGS.update(c.league_settings())

    # Players (meta from rosters + free agents page)
    meta = c.player_meta_from_rosters()
    for pid, pdata in meta.items():
        store.PLAYERS[pid] = {
            "id": pid,
            "name": pdata.get("name", pid),
            "pos": pdata.get("pos", "WR"),
            "team": pdata.get("team", "FA"),
            "bye_week": pdata.get("bye_week", None),
        }

    return {
        "teams": len(store.TEAMS),
        "rosters": sum(len(v) for v in store.ROSTERS.values()),
        "players": len(store.PLAYERS),
        "settings": True,
    }

def delta_sync() -> Dict[str, Any]:
    # MVP: re-run full sync (fast enough). Later: diff by recent transactions.
    return full_sync()
