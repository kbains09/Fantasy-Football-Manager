from typing import Dict, Any
from services.projections.registry import get_source
from services.mock_data import PLAYERS, SETTINGS
from services.valuation import compute_vorp_for_week

# simple in-memory valuation cache by week
_VALUATIONS_CACHE: Dict[int, Dict[str, Any]] = {}

def compute_valuations_task(week: int | None, source: str | None):
    w = week or 1
    src = get_source(source or "mock")
    if not src:
        raise ValueError(f"unknown source '{source}'")
    projections = src.weekly_points(PLAYERS, week=w)
    vals = compute_vorp_for_week(PLAYERS, projections, SETTINGS, w)
    _VALUATIONS_CACHE[w] = vals
    # result_ref can be used to indicate what changed
    return {"kind": "valuations", "week": w, "count": len(vals)}

def get_cached_valuations(week: int) -> Dict[str, Any] | None:
    return _VALUATIONS_CACHE.get(week)
