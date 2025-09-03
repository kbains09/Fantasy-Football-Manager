from fastapi import APIRouter
from services.projections.registry import list_sources

router = APIRouter()

@router.get("/projections/sources")
def sources():
    return list_sources()
