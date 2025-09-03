from fastapi import APIRouter, HTTPException
import os
import re
from adapters.espn.client import is_available, ESPNClient
from adapters.espn.sync import full_sync, delta_sync

router = APIRouter()
_GUID_RE = re.compile(r"\{[0-9a-fA-F-]{36}\}")

def _require_env():
    lid = os.getenv("ESPN_LEAGUE_ID")
    yr  = os.getenv("ESPN_YEAR")
    if not lid or not yr:
        raise HTTPException(
            status_code=400,
            detail="Missing ESPN_LEAGUE_ID or ESPN_YEAR in environment (.env)."
        )

def _extract_owner_ids(owner_obj) -> list[str]:
    """
    Try very hard to extract ESPN owner IDs (GUIDs with braces) from
    owner objects / dicts / strings.
    """
    if owner_obj is None:
        return []
    ids: list[str] = []

    def add_matches(s: str):
        for m in _GUID_RE.findall(s):
            ids.append(m.strip("{}").upper())

    # espn_api sometimes returns list of dict-like owners
    if isinstance(owner_obj, (list, tuple)):
        for o in owner_obj:
            if isinstance(o, dict):
                # try common keys
                for k in ("id", "ID"):
                    v = o.get(k)
                    if v:
                        add_matches(str(v))
                # also search whole dict repr
                add_matches(str(o))
            else:
                add_matches(str(o))
    elif isinstance(owner_obj, dict):
        for k in ("id", "ID"):
            v = owner_obj.get(k)
            if v:
                add_matches(str(v))
        add_matches(str(owner_obj))
    else:
        add_matches(str(owner_obj))

    # de-dupe
    return sorted(set(ids))

@router.get("/sync/espn/check")
def sync_espn_check():
    if not is_available():
        raise HTTPException(status_code=503, detail="espn-api not installed")
    _require_env()
    try:
        c = ESPNClient()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ESPN config error: {e}")

    my_tid = None
    swid = (os.getenv("ESPN_SWID") or "").strip()
    swid_core = swid.strip("{}").upper()
    manual_override = os.getenv("ESPN_MY_TEAM_ID")

    info = []
    for t in c.league.teams:
        owners_raw = getattr(t, "owners", None) or getattr(t, "owner", None)
        owner_ids = _extract_owner_ids(owners_raw)
        hit = swid_core and (swid_core in owner_ids)
        tid = f"espn-{t.team_id}"
        if hit:
            my_tid = tid
        info.append({"id": tid, "name": t.team_name, "owner_ids": owner_ids})

    # env override if set
    if not my_tid and manual_override:
        my_tid = manual_override

    return {
        "ok": True,
        "league_id": c.league_id,
        "year": c.year,
        "detected_my_team_id": my_tid,
        "teams": info,
        "needs_private_cookies": (c.espn_s2 is None or c.swid is None),
        "used_env_override": bool(manual_override and my_tid == manual_override),
    }

@router.post("/sync/espn/full")
def sync_espn_full():
    if not is_available():
        raise HTTPException(status_code=503, detail="espn-api not installed")
    _require_env()
    return {"ok": True, "synced": full_sync()}

@router.post("/sync/espn/delta")
def sync_espn_delta():
    if not is_available():
        raise HTTPException(status_code=503, detail="espn-api not installed")
    _require_env()
    return {"ok": True, "synced": delta_sync()}

@router.get("/teams/mine")
def my_team_id():
    """
    Convenience endpoint: returns your team id based on SWID or ESPN_MY_TEAM_ID.
    """
    if not is_available():
        raise HTTPException(status_code=503, detail="espn-api not installed")
    _require_env()
    c = ESPNClient()

    swid_core = (os.getenv("ESPN_SWID") or "").strip().strip("{}").upper()
    manual_override = os.getenv("ESPN_MY_TEAM_ID")
    for t in c.league.teams:
        owners_raw = getattr(t, "owners", None) or getattr(t, "owner", None)
        if swid_core and swid_core in _extract_owner_ids(owners_raw):
            return {"team_id": f"espn-{t.team_id}", "source": "swid"}
    if manual_override:
        return {"team_id": manual_override, "source": "env"}
    raise HTTPException(status_code=404, detail="Could not detect your team; set ESPN_SWID or ESPN_MY_TEAM_ID")
