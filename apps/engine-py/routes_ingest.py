"""League data ingestion endpoints."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["ingest"])


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------


class TeamIngest(BaseModel):
    """Team data for ingestion."""

    id: str
    name: str
    manager: Optional[str] = None


class RosterIngest(BaseModel):
    """Roster slot data for ingestion."""

    team_id: str
    player_id: str
    slot: str = Field(description="Lineup slot: QB/RB/WR/TE/FLEX/BN/IR")


class LeagueIngestRequest(BaseModel):
    """Full league data payload for ingestion."""

    teams: List[TeamIngest]
    rosters: List[RosterIngest]
    settings: Dict[str, Any] = Field(
        description="League settings: scoring_json, roster_rules_json, faab_budget, etc."
    )


# -----------------------------------------------------------------------------
# In-Memory Store (MVP - will be replaced with database)
# -----------------------------------------------------------------------------

_LAST_INGEST: Dict[str, Any] = {}


def get_last_ingest() -> Dict[str, Any]:
    """Access the last ingested league data (for other modules)."""
    return _LAST_INGEST


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.post("/ingest/league", status_code=204)
def ingest_league(body: LeagueIngestRequest) -> None:
    """
    Ingest league data (teams, rosters, settings).

    Currently stores in-memory for demo purposes.
    TODO: Upsert to database via Store class.
    """
    try:
        _LAST_INGEST.clear()
        _LAST_INGEST.update(body.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ingest failed: {e}")