from typing import List, Dict, Any, Tuple

def _is_starter(slot: str) -> bool:
    return slot in ("QB", "RB", "WR", "TE", "FLEX")

def compute_team_score(
    roster_items: List[Dict[str, Any]],
    treat_flex_as: Tuple[str, ...] = ("RB", "WR", "TE"),
) -> float:
    """
    Sum starter valuations; for FLEX choose the best from allowed positions.
    roster_items: [{"player": {...}, "slot": "RB", "valuation": {...}}, ...]
    """
    total = 0.0

    # First: take fixed slots (QB, RB, WR, TE). Track candidates for FLEX.
    flex_candidates = []
    used: set[str] = set()

    for item in roster_items:
        slot = item.get("slot")
        player = item.get("player") or {}
        pid = player.get("id")
        val = item.get("valuation") or {}
        vorp = float(val.get("vorp") or 0.0)

        if slot in ("QB", "RB", "WR", "TE"):
            total += max(0.0, vorp)  # don't penalize below replacement
            used.add(pid)
        elif slot == "FLEX" and player.get("pos") in treat_flex_as:
            flex_candidates.append((pid, vorp))
        # BN/IR ignored

    if flex_candidates:
        # pick top remaining candidate for FLEX
        flex_candidates.sort(key=lambda x: x[1], reverse=True)
        for pid, vorp in flex_candidates:
            if pid not in used:
                total += max(0.0, vorp)
                break

    return round(total, 2)
