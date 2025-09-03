from typing import Dict, Any, List
from .mock import MockSource

# Register available sources here
_SOURCES = {
    "mock": MockSource(),
}

def list_sources() -> List[Dict[str, Any]]:
    return [
        {"id": s.id, "name": s.name, "description": s.description}
        for s in _SOURCES.values()
    ]

def get_source(source_id: str):
    return _SOURCES.get(source_id)
