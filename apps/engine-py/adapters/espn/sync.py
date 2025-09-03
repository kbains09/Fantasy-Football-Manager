# apps/engine-py/adapters/espn/sync.py
from __future__ import annotations
from typing import Dict, Any
from .client import ESPNClient
from services import store

__all__ = ["full_sync", "delta_sync"]

def _write_league_to_store(c: ESPNClient) -> Dict[str, Any]:
    """
    Idempotently writes league snapshot into the canonical in-memory store.
    Returns basic counts for diagnostics.
    """
    # clear and re-fill for now (MVP). later: make this incremental.
    if hasattr(store, "reset"):
        store.reset()
    else:
        store.PLAYERS.clear()
        store.TEAMS.clear()
        store.ROSTERS.clear()

    # Teams
    for t in c.league.teams:
        tid = f"espn-{t.team_id}"
        store.TEAMS[tid] = {
            "id": tid,
            "name": t.team_name,
            "manager": getattr(t, "owners", getattr(t, "owner", None)),
        }

    # Rosters (normalized)
    store.ROSTERS.clear()
    for row in c.rosters():
        store.ROSTERS.setdefault(row["team_id"], []).append(
            {"player_id": row["player_id"], "slot": row["slot"]}
        )

    # Players meta
    meta = c.player_meta_from_rosters()
    for pid, pdata in meta.items():
        store.PLAYERS[pid] = {
            "id": pid,
            "name": pdata.get("name", pid),
            "pos": pdata.get("pos", "WR"),
            "team": pdata.get("team", "FA"),
            "bye_week": pdata.get("bye_week"),
        }

    # Settings
    store.SETTINGS.update(c.league_settings())

    return {
        "teams": len(store.TEAMS),
        "rosters": sum(len(v) for v in store.ROSTERS.values()),
        "players": len(store.PLAYERS),
        "settings": True,
    }

def full_sync() -> Dict[str, Any]:
    """
    Full refresh from ESPN into services.store.
    """
    c = ESPNClient()
    return _write_league_to_store(c)

def delta_sync() -> Dict[str, Any]:
    """
    MVP delta: call full_sync(). Later, switch to only applying recent transactions.
    Kept separate so routes can call /delta on a schedule without changing clients.
    """
    return full_sync()
