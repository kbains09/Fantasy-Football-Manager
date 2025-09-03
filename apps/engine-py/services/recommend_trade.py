from typing import Dict, Any, List, Tuple

def simple_one_for_one_trades(
    players: Dict[str, Dict[str, Any]],
    your_roster: List[Dict[str, str]],      # [{player_id, slot}]
    opp_roster: List[Dict[str, str]],
    valuations: Dict[str, Dict[str, Any]],  # {pid: {vorp, ...}}
    max_offers: int = 2,
) -> List[Dict[str, Any]]:
    """
    Very simple: try swapping your weakest starter at a position for their strongest bench
    that (a) helps you in that pos and (b) doesn't hurt them overall (delta_them >= 0),
    ideally improves them too.
    """
    def starters(roster):  # pids for starters only
        return [r["player_id"] for r in roster if r["slot"] in ("QB", "RB", "WR", "TE")]

    def bench(roster):
        return [r["player_id"] for r in roster if r["slot"] in ("BN", "IR")]

    def vorp(pid: str) -> float:
        return float(valuations.get(pid, {}).get("vorp") or 0.0)

    your_starters = starters(your_roster)
    their_bench = bench(opp_roster)

    # pick your weakest starter (lowest VORP), and find an opponent bench upgrade
    candidates: List[Tuple[str, str, float, float, float]] = []  # (give, get, delta_you, delta_them, their_gain)
    if not your_starters or not their_bench:
        return []

    weakest = sorted(your_starters, key=vorp)[0]
    w_v = vorp(weakest)

    for pid in their_bench:
        get_v = vorp(pid)
        delta_you = max(0.0, get_v - w_v)

        # approximate opponent delta: they lose bench pid, don't affect starters (0)
        # (MVP: we don't simulate their lineup; assume losing a bench piece is small negative)
        delta_them = -min(0.5, max(0.0, get_v * 0.1))  # small cost to them
        their_gain = -delta_them

        if delta_you > 0 and delta_them >= -0.1:  # near-neutral for them
            candidates.append((weakest, pid, round(delta_you, 2), round(delta_them, 2), round(their_gain, 2)))

    # sort by your delta, then least harm to them
    candidates.sort(key=lambda t: (t[2], -t[3]), reverse=True)
    offers = []
    for give, get, d_you, d_them, g_them in candidates[:max_offers]:
        offers.append({
            "opponent_team_id": "UNKNOWN",  # fill at call site
            "give": [give],
            "get": [get],
            "delta_you": d_you,
            "delta_them": d_them,
            "rationale": f"Swap {give} for {get}: you +{d_you:.2f} VORP; them {d_them:.2f}.",
        })
    return offers
