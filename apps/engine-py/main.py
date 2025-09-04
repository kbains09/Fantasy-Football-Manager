from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import routes_health
import routes_sources
import routes_compute
import routes_jobs
import routes_players
import routes_teams
import routes_ingest
import routes_recommend
import routes_sync_espn
import routes_lineup


import config

def create_app() -> FastAPI:
    app = FastAPI(title="FantasyManager Engine", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = "/v1"
    app.include_router(routes_health.router,     prefix=api)
    app.include_router(routes_sources.router,    prefix=api)
    app.include_router(routes_compute.router,    prefix=api)
    app.include_router(routes_jobs.router,       prefix=api)
    app.include_router(routes_players.router,    prefix=api)
    app.include_router(routes_teams.router,      prefix=api)
    app.include_router(routes_ingest.router,     prefix=api)
    app.include_router(routes_recommend.router,  prefix=api)
    app.include_router(routes_sync_espn.router, prefix=api)
    app.include_router(routes_lineup.router, prefix=api)



    return app

# uvicorn main:app --reload
app = create_app()
