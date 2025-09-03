# apps/engine-py/adapters/espn/client.py
from __future__ import annotations
import os
from typing import Any, Dict, List

# --- soft import so server keeps running if package missing ---
try:
    from espn_api.football import League  # type: ignore
    _ESPN_AVAILABLE = True
except Exception as _e:  # ImportError or anything else
    League = None  # type: ignore
    _ESPN_AVAILABLE = False
    _ESPN_IMPORT_ERR = _e

def is_available() -> bool:
    return _ESPN_AVAILABLE

class ESPNClient:
    def __init__(self, league_id: int | None = None, year: int | None = None,
                 espn_s2: str | None = None, swid: str | None = None):
        if not _ESPN_AVAILABLE:
            raise ImportError(f"espn-api not available: {_ESPN_IMPORT_ERR}")
        self.league_id = league_id or int(os.getenv("ESPN_LEAGUE_ID", "0"))
        self.year = year or int(os.getenv("ESPN_YEAR", "0"))
        self.espn_s2 = espn_s2 or os.getenv("ESPN_S2")
        self.swid = swid or os.getenv("ESPN_SWID")
        if not (self.league_id and self.year):
            raise ValueError("ESPN_LEAGUE_ID and ESPN_YEAR are required")
        self.league = League(league_id=self.league_id, year=self.year,
                             espn_s2=self.espn_s2, swid=self.swid)

    # -------- Reads (same as before) --------
    def league_settings(self) -> Dict[str, Any]:
        return {
            "scoring_json": {},
            "roster_rules_json": self._roster_rules(),
            "faab_budget": getattr(self.league.settings, "acquisitionBudget", None),
        }

    def teams(self) -> List[Dict[str, Any]]:
        out = []
        for t in self.league.teams:
            out.append({
                "id": f"espn-{t.team_id}",
                "name": t.team_name,
                "manager": getattr(t, "owner", None) or getattr(t, "owners", None),
            })
        return out

    def rosters(self) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        def norm_slot(s: str) -> str:
            if not s:
                return "BN"
            s = str(s).upper().replace(" ", "")
            # common normalizations
            mapping = {
                "BE": "BN", "BENCH": "BN",
                "IR": "IR",
                "FLEX": "FLEX", "RB/WR/TE": "FLEX", "RBWRTE": "FLEX",
                "D/ST": "DST", "DST": "DST", "DEF": "DST", "D": "DST",
                "K": "K",
                "QB":"QB","RB":"RB","WR":"WR","TE":"TE",
            }
            return mapping.get(s, s)

        for t in self.league.teams:
            for p in t.roster:
                raw_slot = getattr(p, "lineupSlot", None) or getattr(p, "position", None) or "BN"
                slot_norm = norm_slot(str(raw_slot))
                out.append({"team_id": f"espn-{t.team_id}", "player_id": self._pid(p), "slot": slot_norm})
        return out

    def transactions(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for tr in self.league.recent_activity():  # type: ignore
            out.append({
                "id": getattr(tr, "transaction_id", None),
                "type": getattr(tr, "type", None),
                "date": getattr(tr, "date", None),
            })
        return out

    # ----- Player meta (used by sync to map to our schema) -----
    def player_meta_from_rosters(self) -> Dict[str, Dict[str, Any]]:
        meta: Dict[str, Dict[str, Any]] = {}
        for t in self.league.teams:
            for p in t.roster:
                pid = self._pid(p)
                meta[pid] = {
                    "id": pid,
                    "name": getattr(p, "name", pid),
                    "pos": self._map_pos(getattr(p, "defaultPosition", getattr(p, "position", None))),
                    "team": self._map_team(getattr(p, "proTeam", getattr(p, "proTeamAbbrev", None))),
                    "bye_week": getattr(p, "bye_week", None),
                }
        # Optionally pull a page of free agents to enrich pool:
        try:
            for p in self.league.free_agents(size=100):  # type: ignore
                pid = self._pid(p)
                meta.setdefault(pid, {
                    "id": pid,
                    "name": getattr(p, "name", pid),
                    "pos": self._map_pos(getattr(p, "defaultPosition", getattr(p, "position", None))),
                    "team": self._map_team(getattr(p, "proTeam", getattr(p, "proTeamAbbrev", None))),
                    "bye_week": getattr(p, "bye_week", None),
                })
        except Exception:
            pass
        return meta

    # ----- Helpers -----
    @staticmethod
    def _pid(player_obj) -> str:
        return f"espn-p{getattr(player_obj, 'playerId', getattr(player_obj, 'id', '0'))}"

    def _roster_rules(self) -> Dict[str, int]:
        rs = getattr(self.league.settings, "roster_settings", {})
        def g(key, default):
            return int(getattr(rs, key, default)) if hasattr(rs, key) else int(rs.get(key, default)) if isinstance(rs, dict) else default
        return {"QB": g("qb", 1), "RB": g("rb", 2), "WR": g("wr", 2), "TE": g("te", 1), "FLEX": g("flex", 1), "BN": g("bench", 6)}

    # --- Mapping helpers (ESPN -> our enums) ---
    @staticmethod
    def _map_pos(value) -> str:
        if value is None:
            return "WR"
        s = str(value).upper()
        # ESPN sometimes gives "D/ST", "DST", or integer ids; we normalize:
        if "DST" in s or "D/ST" in s or s in {"DEF", "D"}:
            return "DST"
        if "QB" in s:
            return "QB"
        if "RB" in s:
            return "RB"
        if "WR" in s:
            return "WR"
        if "TE" in s:
            return "TE"
        if "K" in s or "PK" in s:
            return "K"
        # fallback
        return "WR"

    @staticmethod
    def _map_team(value) -> str:
        if value is None:
            return "FA"
        s = str(value).upper()
        # Handle both full names and abbrevs len>=2 (quick map)
        # Common ESPN abbreviations:
        m = {
            "ARI":"ARI","ATL":"ATL","BAL":"BAL","BUF":"BUF","CAR":"CAR","CHI":"CHI","CIN":"CIN","CLE":"CLE",
            "DAL":"DAL","DEN":"DEN","DET":"DET","GB":"GB","HOU":"HOU","IND":"IND","JAX":"JAX","KC":"KC",
            "LV":"LV","LAC":"LAC","LAR":"LAR","MIA":"MIA","MIN":"MIN","NE":"NE","NO":"NO","NYG":"NYG",
            "NYJ":"NYJ","PHI":"PHI","PIT":"PIT","SEA":"SEA","SF":"SF","TB":"TB","TEN":"TEN","WAS":"WAS",
        }
        # Sometimes you get full names like "49ers" or "San Francisco 49ers"
        for abbr in m:
            if s == abbr or abbr in s:
                return abbr
        # final fallback
        return s[:3]
