from typing import Dict, Any, List, Tuple
from .valuation import compute_vorp_for_week

def recommend_free_agents(
    players: Dict[str, Dict[str, Any]],
    current_roster: List[Dict[str, str]],  # [{player_id, slot}]
    free_agents: List[str],
    projections: Dict[str, float],
    settings: Dict[str, Any],
    week: int,
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """
    For each FA, simulate replacing your worst starter at the same position (or into FLEX).
    Return items: {player_id, delta_value, suggested_faab, rationale}
    """
    valuations = compute_vorp_for_week(players, projections, settings, week)
    # Build current roster view with valuations
    roster_items = [
        {"player": players[p["player_id"]], "slot": p["slot"], "valuation": valuations.get(p["player_id"])}
        for p in current_roster if p["player_id"] in players
    ]

    # Find worst starter by position for quick delta estimates
    def starter_vorps(pos: str) -> List[Tuple[str, float]]:
        return [
            (ri["player"]["id"], float((ri["valuation"] or {}).get("vorp") or 0.0))
            for ri in roster_items
            if ri["slot"] in ("QB", "RB", "WR", "TE") and ri["player"]["pos"] == pos
        ]

    suggestions: List[Dict[str, Any]] = []
    for pid in free_agents:
        p = players.get(pid)
        if not p:
            continue
        pos = p["pos"]
        fa_vorp = float(valuations.get(pid, {}).get("vorp") or 0.0)

        worst_same = sorted(starter_vorps(pos), key=lambda x: x[1])[0] if starter_vorps(pos) else None
        if worst_same is None:
            # If you don't start this pos, maybe FLEX (RB/WR/TE only)
            if pos not in ("RB", "WR", "TE"):
                continue
            worst_flexable = sorted(
                starter_vorps("RB") + starter_vorps("WR") + starter_vorps("TE"),
                key=lambda x: x[1]
            )[0] if (starter_vorps("RB") or starter_vorps("WR") or starter_vorps("TE")) else None
            replace_id, replace_vorp = worst_flexable if worst_flexable else (None, 0.0)
        else:
            replace_id, replace_vorp = worst_same

        delta = round(max(0.0, fa_vorp - replace_vorp), 2)
        if delta <= 0:
            continue

        # naive FAAB suggestion: 3x delta, clamp 1..25
        suggested_faab = int(min(25, max(1, round(delta * 3))))

        rationale = f"{p['name']} ({pos}) beats your worst {pos} by +{delta:.2f} VORP."
        if worst_same is None and pos in ("RB", "WR", "TE"):
            rationale = f"{p['name']} ({pos}) improves your FLEX over your weakest starter by +{delta:.2f} VORP."

        suggestions.append({
            "player_id": pid,
            "delta_value": delta,
            "suggested_faab": suggested_faab,
            "rationale": rationale,
        })

    suggestions.sort(key=lambda s: s["delta_value"], reverse=True)
    return suggestions[:top_n]
