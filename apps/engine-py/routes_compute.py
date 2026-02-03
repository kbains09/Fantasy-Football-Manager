"""Compute endpoints for triggering background valuation jobs."""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jobs.queue import enqueue
from jobs.tasks import compute_valuations_task
from services.projections.registry import get_source

router = APIRouter(tags=["compute"])


class ComputeValuationsRequest(BaseModel):
    """Request body for triggering valuation computation."""

    week: Optional[int] = None
    source: Optional[str] = None


@router.post("/compute/valuations", status_code=202)
def compute_valuations(body: ComputeValuationsRequest) -> dict:
    """
    Trigger async valuation computation job.

    Returns a job_id that can be polled via GET /jobs/{job_id}.
    """
    src = body.source or "mock"
    if not get_source(src):
        raise HTTPException(status_code=400, detail=f"Unknown projection source: '{src}'")

    job_id = enqueue(compute_valuations_task, kwargs={"week": body.week, "source": src})
    return {"job_id": job_id}