def compute_valuations_task(week: int | None, source: str | None):
    # TODO: pull projections via services.projections.mock, compute VORP, persist to DB
    # For now, return a tiny result reference for the UI to show something.
    return {"kind": "valuations", "week": week or 1, "source": source or "mock"}
