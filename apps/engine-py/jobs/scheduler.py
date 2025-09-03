from apscheduler.schedulers.background import BackgroundScheduler
from adapters.espn.sync import delta_sync
from jobs.queue import enqueue
from jobs.tasks import compute_valuations_task

sched: BackgroundScheduler | None = None

def start():
    global sched
    if sched:  # already started
        return
    sched = BackgroundScheduler(timezone="UTC")
    # every 15 min: pull latest league changes
    sched.add_job(delta_sync, "interval", minutes=15, id="espn-delta")
    # every 15 min: recompute valuations for week 1 (replace with current week logic)
    sched.add_job(lambda: enqueue(compute_valuations_task, kwargs={"week": 1, "source": "mock"}),
                  "interval", minutes=15, id="valuations")
    sched.start()
