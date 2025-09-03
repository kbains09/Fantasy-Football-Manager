from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from jobs.queue import enqueue
from jobs.tasks import compute_valuations_task
from services.projections.registry import get_source

class ComputeBody(BaseModel):
    week: int | None = None
    source: str | None = None

router = APIRouter()

@router.post("/compute/valuations", status_code=202)
def compute(body: ComputeBody):
    src = body.source or "mock"
    if not get_source(src):
        raise HTTPException(status_code=400, detail=f"unknown source '{src}'")
    jid = enqueue(compute_valuations_task, kwargs={"week": body.week, "source": src})
    return {"job_id": jid}
