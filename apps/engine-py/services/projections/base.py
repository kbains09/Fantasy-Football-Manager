from typing import Dict, Any, Protocol

class ProjectionSource(Protocol):
    id: str
    name: str
    description: str

    def weekly_points(self, players: Dict[str, Dict[str, Any]], *, week: int) -> Dict[str, float]:
        """Return projected fantasy points for each player_id for the given week."""
        ...
