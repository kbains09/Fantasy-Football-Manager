from typing import Dict, Any
import hashlib

# tiny deterministic helper
def _hash01(key: str) -> float:
    h = hashlib.md5(key.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF

_BASE_BY_POS = {"QB": 18.0, "RB": 12.0, "WR": 11.0, "TE": 8.0}

class MockSource:
    id = "mock"
    name = "Mock"
    description = "Deterministic dev source for projections"

    def weekly_points(self, players: Dict[str, Dict[str, Any]], *, week: int) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for pid, p in players.items():
            pos = p.get("pos", "")
            base = _BASE_BY_POS.get(pos, 0.0)
            noise = _hash01(f"{pid}:{week}:{self.id}") * 6.0  # ± ~6 pts
            out[pid] = base + noise
        return out
