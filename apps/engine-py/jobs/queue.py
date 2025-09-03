import time
import uuid
from typing import Dict, Literal

Status = Literal["queued", "running", "done", "failed"]
_jobs: Dict[str, dict] = {}

def enqueue(func, *, args=(), kwargs=None) -> str:
    jid = str(uuid.uuid4())
    _jobs[jid] = {"id": jid, "status": "queued", "created_at": time.time(), "updated_at": time.time(), "error": None}
    # naive async: run in thread for now
    import threading
    def _run():
        _jobs[jid]["status"] = "running"
        _jobs[jid]["updated_at"] = time.time()
        try:
            res = func(*args, **(kwargs or {}))
            _jobs[jid]["status"] = "done"
            _jobs[jid]["result_ref"] = res
        except Exception as e:
            _jobs[jid]["status"] = "failed"
            _jobs[jid]["error"] = {"error": str(e)}
        finally:
            _jobs[jid]["updated_at"] = time.time()
    threading.Thread(target=_run, daemon=True).start()
    return jid

def get(jid: str) -> dict | None:
    job = _jobs.get(jid)
    if not job:
        return None
    return {
        "id": job["id"],
        "status": job["status"],
        "created_at": _iso(job["created_at"]),
        "updated_at": _iso(job["updated_at"]),
        "result_ref": job.get("result_ref"),
        "error": job.get("error"),
    }

def _iso(ts: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
