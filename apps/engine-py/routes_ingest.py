from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

router = APIRouter()

class Team(BaseModel):
    id: str
    name: str
    manager: Optional[str] = None

class Roster(BaseModel):
    team_id: str
    player_id: str
    slot: str = Field(description="QB/RB/WR/TE/FLEX/BN/IR")

class LeagueIngest(BaseModel):
    teams: List[Team]
    rosters: List[Roster]
    settings: Dict[str, Any] = Field(
        description="scoring_json, roster_rules_json, faab_budget, etc."
    )

# For now we stash the last ingested payload (in-memory) so UI can proceed.
_LAST_INGEST: Dict[str, Any] = {}

@router.post("/ingest/league", status_code=204)
def ingest_league(body: LeagueIngest):
    try:
        # TODO: upsert teams, rosters, settings into DB
        _LAST_INGEST.clear()
        _LAST_INGEST.update(body.model_dump())
        return
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ingest failed: {e}")
