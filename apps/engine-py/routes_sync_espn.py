"""ESPN league synchronization endpoints."""
import os
import re
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException

from adapters.espn.client import ESPNClient, is_available
from adapters.espn.sync import delta_sync, full_sync

router = APIRouter(tags=["espn"])

# Regex to match ESPN owner GUIDs (with braces)
_GUID_PATTERN = re.compile(r"\{[0-9a-fA-F-]{36}\}")


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def _require_espn_env() -> None:
    """Raise 400 if required ESPN environment variables are missing."""
    league_id = os.getenv("ESPN_LEAGUE_ID")
    year = os.getenv("ESPN_YEAR")

    if not league_id or not year:
        raise HTTPException(
            status_code=400,
            detail="Missing ESPN_LEAGUE_ID or ESPN_YEAR in environment. "
            "Add them to apps/engine-py/.env",
        )


def _require_espn_available() -> None:
    """Raise 503 if espn-api package is not installed."""
    if not is_available():
        raise HTTPException(
            status_code=503,
            detail="espn-api package not installed. Run: pip install espn-api",
        )


def _get_espn_client() -> ESPNClient:
    """Create ESPN client, raising 400 on configuration errors."""
    try:
        return ESPNClient()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ESPN configuration error: {e}")


def _extract_owner_ids(owner_obj: Any) -> List[str]:
    """
    Extract ESPN owner IDs (GUIDs) from various owner object formats.

    The espn-api library returns owner data in inconsistent formats:
    - List of dicts with 'id' key
    - Single dict with 'id' key
    - String representation containing GUIDs

    This function tries all approaches to reliably extract owner IDs.

    Args:
        owner_obj: Owner data in any format from espn-api

    Returns:
        Sorted list of unique owner ID strings (without braces, uppercase)
    """
    if owner_obj is None:
        return []

    ids: List[str] = []

    def add_guid_matches(text: str) -> None:
        """Find all GUIDs in a string and add them to ids list."""
        for match in _GUID_PATTERN.findall(text):
            ids.append(match.strip("{}").upper())

    # Handle list/tuple of owners
    if isinstance(owner_obj, (list, tuple)):
        for owner in owner_obj:
            if isinstance(owner, dict):
                # Try common key names
                for key in ("id", "ID"):
                    value = owner.get(key)
                    if value:
                        add_guid_matches(str(value))
                # Also search string representation
                add_guid_matches(str(owner))
            else:
                add_guid_matches(str(owner))

    # Handle single dict
    elif isinstance(owner_obj, dict):
        for key in ("id", "ID"):
            value = owner_obj.get(key)
            if value:
                add_guid_matches(str(value))
        add_guid_matches(str(owner_obj))

    # Handle string or other types
    else:
        add_guid_matches(str(owner_obj))

    # Return deduplicated, sorted list
    return sorted(set(ids))


def _get_swid_core() -> str:
    """Get the normalized SWID (without braces, uppercase)."""
    swid = os.getenv("ESPN_SWID") or ""
    return swid.strip().strip("{}").upper()


def _detect_my_team(client: ESPNClient) -> Optional[str]:
    """
    Detect the current user's team based on SWID cookie.

    Returns team ID (e.g., 'espn-5') if found, None otherwise.
    """
    swid_core = _get_swid_core()
    if not swid_core:
        return None

    for team in client.league.teams:
        owners_raw = getattr(team, "owners", None) or getattr(team, "owner", None)
        owner_ids = _extract_owner_ids(owners_raw)

        if swid_core in owner_ids:
            return f"espn-{team.team_id}"

    return None


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.get("/sync/espn/check")
def check_espn_connection() -> dict:
    """
    Verify ESPN connection and detect your team.

    Validates ESPN credentials, lists all teams in the league,
    and attempts to detect which team belongs to you based on SWID.
    """
    _require_espn_available()
    _require_espn_env()

    client = _get_espn_client()
    manual_override = os.getenv("ESPN_MY_TEAM_ID")

    # Build team info list and detect user's team
    teams_info = []
    detected_team_id = None

    for team in client.league.teams:
        owners_raw = getattr(team, "owners", None) or getattr(team, "owner", None)
        owner_ids = _extract_owner_ids(owners_raw)
        team_id = f"espn-{team.team_id}"

        # Check if this is the user's team
        swid_core = _get_swid_core()
        if swid_core and swid_core in owner_ids:
            detected_team_id = team_id

        teams_info.append({
            "id": team_id,
            "name": team.team_name,
            "owner_ids": owner_ids,
        })

    # Fall back to manual override if SWID detection failed
    if not detected_team_id and manual_override:
        detected_team_id = manual_override

    return {
        "ok": True,
        "league_id": client.league_id,
        "year": client.year,
        "detected_my_team_id": detected_team_id,
        "teams": teams_info,
        "needs_private_cookies": client.espn_s2 is None or client.swid is None,
        "used_env_override": bool(manual_override and detected_team_id == manual_override),
    }


@router.post("/sync/espn/full")
def sync_full() -> dict:
    """
    Perform full league sync from ESPN.

    Fetches all teams, rosters, and players from ESPN and populates
    the in-memory data store. Previous data is replaced.
    """
    _require_espn_available()
    _require_espn_env()

    result = full_sync()
    return {"ok": True, "synced": result}


@router.post("/sync/espn/delta")
def sync_delta() -> dict:
    """
    Perform incremental sync from ESPN.

    Currently performs a full sync. Reserved for future incremental
    updates based on recent transactions.
    """
    _require_espn_available()
    _require_espn_env()

    result = delta_sync()
    return {"ok": True, "synced": result}


@router.get("/me/team")
def get_my_team() -> dict:
    """
    Get your team ID.

    Attempts to detect your team using SWID cookie matching.
    Falls back to ESPN_MY_TEAM_ID environment variable if set.

    Returns 404 if team cannot be determined.
    """
    _require_espn_available()
    _require_espn_env()

    client = _get_espn_client()
    manual_override = os.getenv("ESPN_MY_TEAM_ID")

    # Try SWID detection first
    detected_team_id = _detect_my_team(client)

    if detected_team_id:
        return {
            "team_id": detected_team_id,
            "source": "swid",
            "league_id": client.league_id,
            "year": client.year,
        }

    # Fall back to manual override
    if manual_override:
        return {
            "team_id": manual_override,
            "source": "env",
            "league_id": client.league_id,
            "year": client.year,
        }

    # Nothing found
    raise HTTPException(
        status_code=404,
        detail="Could not detect your team. "
        "Set ESPN_SWID (with braces) or ESPN_MY_TEAM_ID in your .env file.",
    )