"""Projection source listing endpoints."""
from typing import List

from fastapi import APIRouter

from services.projections.registry import list_sources

router = APIRouter(tags=["projections"])


@router.get("/projections/sources")
def get_projection_sources() -> List[dict]:
    """
    List available projection sources.

    Returns all registered projection providers that can be used
    for valuation calculations.
    """
    return list_sources()