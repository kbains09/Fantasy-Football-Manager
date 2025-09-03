from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List, Tuple
from services import store
from services.projections.registry import get_source
from services.valuation import compute_vorp_for_week

router = APIRouter()

FLEX_POS = ("RB", "WR", "TE")

def _recommend_lineup(roster_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    pool: List[Tuple[str, float, Dict[str, Any]]] = []
    for it in roster_items:
        if (it.get("slot") or "").upper() == "IR":
            continue
        pos = (it.get("player") or {}).get("pos")
        val = (it.get("valuation") or {}).get("vorp")
        score = float(val) if isinstance(val, (int, float)) else -999.0
        pool.append((pos, score, it))
    pool.sort(key=lambda x: x[1], reverse=True)

    used: set[str] = set()
    starters: List[Dict[str, Any]] = []

    def take(predicate, label, count=1):
        nonlocal pool
        taken = 0
        i = 0
        while i < len(pool) and taken < count:
            pos, score, it = pool[i]
            pid = (it.get("player") or {}).get("id")
            if pid not in used and predicate(pos):
                starters.append({"slot": label, "player": it["player"], "valuation": it.get("valuation")})
                used.add(pid)
                pool.pop(i)
                taken += 1
            else:
                i += 1

    take(lambda p: p == "QB", "QB")
    take(lambda p: p == "RB", "RB", 2)
    take(lambda p: p == "WR", "WR", 2)
    take(lambda p: p == "TE", "TE")
    take(lambda p: p in FLEX_POS, "FLEX")

    bench = [it for _, _, it in pool if (it.get("player") or {}).get("id") not in used]
    total_vorp = sum(float((s.get("valuation") or {}).get("vorp") or 0.0) for s in starters)
    return {"starters": starters, "bench": bench, "total_vorp": round(total_vorp, 2)}

@router.get("/recommend/lineup", summary="Recommend Lineup Route")
def recommend_lineup_route(team_id: str, week: Optional[int] = Query(None, ge=1, le=18)):
    w = week or 1
    t = store.team(team_id)
    if not t:
        raise HTTPException(status_code=404, detail="team not found")

    src = get_source("mock")
    projections = src.weekly_points(store.PLAYERS, week=w)
    valuations = compute_vorp_for_week(store.PLAYERS, projections, store.SETTINGS, w)

    roster_view = []
    for slot in store.roster(team_id):
        pid = slot["player_id"]
        player = store.PLAYERS.get(pid)
        valuation = valuations.get(pid)
        roster_view.append({"player": player, "slot": slot["slot"], "valuation": valuation})

    rec = _recommend_lineup(roster_view)
    rec.update({"team": t, "week": w})
    return rec
