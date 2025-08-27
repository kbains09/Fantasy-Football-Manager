# models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, UniqueConstraint

class Base(DeclarativeBase):
    pass

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    manager: Mapped[str | None] = mapped_column(String, nullable=True)

class Player(Base):
    __tablename__ = "players"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    pos: Mapped[str | None] = mapped_column(String, nullable=True)  # RB/WR/TE/QB etc

class Roster(Base):
    __tablename__ = "rosters"
    team_id: Mapped[str] = mapped_column(String, primary_key=True)
    player_id: Mapped[str] = mapped_column(String, primary_key=True)
    slot: Mapped[str] = mapped_column(String, nullable=False)

class Valuation(Base):
    __tablename__ = "valuations"
    player_id: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String, default="baseline")
    week: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("player_id", "source", "week", name="uq_val_source_week"),)
