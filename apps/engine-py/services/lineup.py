from __future__ import annotations
from typing import Dict, Any, List, Tuple

FLEX_POS = ("RB", "WR", "TE")

def recommend_lineup(
    roster_items: List[Dict[str, Any]],   # [{player:{...}, slot:"RB"/"BN"/"IR"... , valuation:{vorp:...}}]
) -> Dict[str, Any]:
    """Return optimal starters and bench from a roster+valuation view."""
    # filter out IR and players w/o valuation (treat missing as very low)
    items: List[Tuple[str, float, Dict[str, Any]]] = []
    for it in roster_items:
        p = it.get("player") or {}
        pos = p.get("pos")
        if it.get("slot", "").upper() == "IR":
            continue
        v = (it.get("valuation") or {}).get("vorp")
        score = float(v) if isinstance(v, (int, float)) else -999.0
        items.append((pos, score, it))

    # sort by score desc
    items.sort(key=lambda x: x[1], reverse=True)

    chosen = {"QB": None, "RB": [], "WR": [], "TE": None, "FLEX": None}
    used_ids: set[str] = set()

    def pick_first(predicate):
        for idx, (pos, score, it) in enumerate(items):
            pid = (it.get("player") or {}).get("id")
            if pid in used_ids:
                continue
            if predicate(pos):
                used_ids.add(pid)
                return items.pop(idx)[2]
        return None

    # Required slots
    chosen["QB"]  = pick_first(lambda pos: pos == "QB")
    chosen["RB"].append(pick_first(lambda pos: pos == "RB"))
    chosen["RB"].append(pick_first(lambda pos: pos == "RB"))
    chosen["WR"].append(pick_first(lambda pos: pos == "WR"))
    chosen["WR"].append(pick_first(lambda pos: pos == "WR"))
    chosen["TE"]  = pick_first(lambda pos: pos == "TE")

    # FLEX (best remaining RB/WR/TE)
    best_flex = pick_first(lambda pos: pos in FLEX_POS)
    chosen["FLEX"] = best_flex

    # Bench = everyone else not used (and not IR)
    bench = []
    for _, _, it in items:
        pid = (it.get("player") or {}).get("id")
        if pid not in used_ids:
            bench.append(it)

    # Flatten result into clean payload
    starters = []
    def add(slot_name: str, it_or_list):
        if isinstance(it_or_list, list):
            for it in it_or_list:
                if it: starters.append({"slot": slot_name, "player": it["player"], "valuation": it.get("valuation")})
        elif it_or_list:
            it = it_or_list
            starters.append({"slot": slot_name, "player": it["player"], "valuation": it.get("valuation")})

    add("QB",  chosen["QB"])
    add("RB",  [x for x in chosen["RB"] if x])
    add("WR",  [x for x in chosen["WR"] if x])
    add("TE",  chosen["TE"])
    add("FLEX",chosen["FLEX"])

    # compute simple total
    total_vorp = sum(float((s.get("valuation") or {}).get("vorp") or 0.0) for s in starters)

    return {"starters": starters, "bench": bench, "total_vorp": round(total_vorp, 2)}
