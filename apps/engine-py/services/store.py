# apps/engine-py/services/store.py
"""
SQLAlchemy-based persistent store.

NOTE: This module defines the production data access layer but is not
currently wired to API routes. Routes use services/mock_data.py for
demonstration purposes. See CONTRIBUTING.md for migration path.
"""

from __future__ import annotations
from typing import Iterable, Sequence
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from db.models import Team, Player, RosterSpot, Valuation, League

class Store:
    def __init__(self, session: Session):
        self.s = session

    # --- Leagues/Teams ---
    def upsert_league(self, league_id: int, year: int, settings: dict | None) -> None:
        league = self.s.get(League, {"id": league_id, "year": year})
        if league is None:
            league = League(id=league_id, year=year, settings=settings)
            self.s.add(league)
        else:
            league.settings = settings

    def upsert_team(self, t: Team) -> None:
        existing = self.s.get(Team, t.id)
        if existing:  # shallow updates OK for MVP
            existing.name = t.name
            existing.league_id = t.league_id
            existing.year = t.year
            existing.owner_ids = t.owner_ids
        else:
            self.s.add(t)

    # --- Players/Rosters ---
    def upsert_players(self, players: Iterable[Player]) -> None:
        for p in players:
            e = self.s.get(Player, p.id)
            if e:
                e.name, e.pos, e.team, e.bye_week, e.ext_id = p.name, p.pos, p.team, p.bye_week, p.ext_id
            else:
                self.s.add(p)

    def replace_roster(self, team_id: str, week: int, spots: list[RosterSpot]) -> None:
        self.s.execute(delete(RosterSpot).where(RosterSpot.team_id==team_id, RosterSpot.week==week))
        for rs in spots:
            self.s.add(rs)

    # --- Reads for endpoints ---
    def get_team(self, team_id: str) -> Team | None:
        return self.s.get(Team, team_id)

    def roster_for_week(self, team_id: str, week: int) -> list[RosterSpot]:
        return list(self.s.scalars(select(RosterSpot).where(RosterSpot.team_id==team_id, RosterSpot.week==week)))

    def valuations_for_week(self, week: int) -> list[Valuation]:
        return list(self.s.scalars(select(Valuation).where(Valuation.week==week)))

    def upsert_valuations(self, vals: Sequence[Valuation]) -> None:
        for v in vals:
            self.s.merge(v)  # relies on uq constraint
