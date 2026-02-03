"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Basic health check - returns ok if the service is running."""
    return {"ok": True}