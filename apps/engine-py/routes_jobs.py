"""Job status endpoints for background task monitoring."""
from fastapi import APIRouter, HTTPException

from jobs.queue import get as get_job

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str) -> dict:
    """
    Get the status of a background job.

    Returns job status (queued/running/done/failed), timestamps, and result or error.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job