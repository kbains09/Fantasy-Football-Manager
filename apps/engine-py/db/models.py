# apps/engine-py/db/models.py
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, ForeignKey, UniqueConstraint, Index, JSON, DateTime

class Base(DeclarativeBase):
    pass

class League(Base):
    __tablename__ = "leagues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)  # ESPN_LEAGUE_ID
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # "espn-12"
    league_id: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    owner_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    __table_args__ = (
        Index("ix_team_league_year", "league_id", "year"),
    )

class Player(Base):
    __tablename__ = "players"
    id: Mapped[str] = mapped_column(String, primary_key=True)     # your canonical id
    ext_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # espn player id, etc.
    name: Mapped[str] = mapped_column(String)
    pos: Mapped[str] = mapped_column(String)  # QB,RB,WR,TE,K,DST
    team: Mapped[str] = mapped_column(String) # NFL abbr (BUF, SF, ...)
    bye_week: Mapped[Optional[int]] = mapped_column(Integer)

class RosterSpot(Base):
    __tablename__ = "roster_spots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    player_id: Mapped[str] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    slot: Mapped[str] = mapped_column(String)  # lineup slot as string (QB,RB,WR,TE,FLEX,BENCH,IR,DST,K)
    week: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        UniqueConstraint("team_id", "player_id", "week", name="uq_roster_entry"),
        Index("ix_roster_team_week", "team_id", "week"),
    )

class Valuation(Base):
    __tablename__ = "valuations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    week: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String, default="mock")
    projected_points: Mapped[float] = mapped_column(Float)
    vorp: Mapped[float] = mapped_column(Float)
    __table_args__ = (
        UniqueConstraint("player_id", "week", "source", name="uq_val_player_week_source"),
        Index("ix_val_week", "week"),
    )

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    type: Mapped[str] = mapped_column(String)  # add, drop, trade, move
    payload: Mapped[dict] = mapped_column(JSON)  # raw snapshot for delta debugging
