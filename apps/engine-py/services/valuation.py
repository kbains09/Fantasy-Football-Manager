from typing import Dict, Any, Tuple
import math
import hashlib

# --- Deterministic mock projections source ---
def _hashf(s: str) -> float:
    # deterministic 0..1
    h = hashlib.md5(s.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF

def base_points_for_pos(pos: str) -> float:
    return {"QB": 18.0, "RB": 12.0, "WR": 11.0, "TE": 8.0}.get(pos, 0.0)

def mock_weekly_projections(players: Dict[str, Dict[str, Any]], *, week: int, source: str) -> Dict[str, float]:
    # Points = base_by_pos + small deterministic noise by (player_id, week, source)
    out: Dict[str, float] = {}
    for pid, p in players.items():
        pos = p.get("pos", "")
        noise = _hashf(f"{pid}:{week}:{source}") * 6.0  # up to ~6 pts variation
        out[pid] = base_points_for_pos(pos) + noise
    return out

# --- Replacement levels & VORP ---
def _starters_required(settings: Dict[str, Any], pos: str) -> int:
    rules = (settings or {}).get("roster_rules_json", {})
    # FLEX reduces replacement level slightly across RB/WR/TE; keep it simple for MVP
    flex = int(rules.get("FLEX", rules.get("FLX", 0)))
    base = int(rules.get(pos, 0))
    if pos in ("RB", "WR", "TE"):
        return base + max(0, math.floor(flex / 3))
    return base

def compute_replacement_levels(
    players: Dict[str, Dict[str, Any]],
    projections: Dict[str, float],
    settings: Dict[str, Any],
    teams_count: int = 12,
) -> Dict[str, float]:
    # For each position, sort projected points and pick the Nth player's points as replacement.
    # N = starters_required(pos) * teams_count
    by_pos: Dict[str, list[Tuple[str, float]]] = {}
    for pid, pts in projections.items():
        pos = players[pid]["pos"]
        by_pos.setdefault(pos, []).append((pid, pts))

    repl: Dict[str, float] = {}
    for pos, arr in by_pos.items():
        arr.sort(key=lambda x: x[1], reverse=True)
        n = max(1, _starters_required(settings, pos) * teams_count)
        idx = min(len(arr) - 1, n - 1)
        repl[pos] = arr[idx][1] if arr else 0.0
    return repl

def compute_vorp_for_week(
    players: Dict[str, Dict[str, Any]],
    projections: Dict[str, float],
    settings: Dict[str, Any],
    week: int,
    teams_count: int = 12,
) -> Dict[str, Dict[str, Any]]:
    repl = compute_replacement_levels(players, projections, settings, teams_count)
    # rank overall
    ranked = sorted(projections.items(), key=lambda kv: kv[1], reverse=True)
    rank_overall_map = {pid: i + 1 for i, (pid, _) in enumerate(ranked)}

    # rank per position
    by_pos: Dict[str, list[Tuple[str, float]]] = {}
    for pid, pts in projections.items():
        pos = players[pid]["pos"]
        by_pos.setdefault(pos, []).append((pid, pts))
    rank_pos_map: Dict[str, int] = {}
    for pos, arr in by_pos.items():
        arr.sort(key=lambda kv: kv[1], reverse=True)
        for i, (pid, _) in enumerate(arr):
            rank_pos_map[pid] = i + 1

    out: Dict[str, Dict[str, Any]] = {}
    for pid, pts in projections.items():
        pos = players[pid]["pos"]
        vorp = round(pts - repl.get(pos, 0.0), 2)
        out[pid] = {
            "player_id": pid,
            "week": week,
            "vorp": vorp,
            "rank_pos": rank_pos_map.get(pid, None),
            "rank_overall": rank_overall_map.get(pid, None),
        }
    return out
