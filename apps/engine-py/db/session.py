# apps/engine-py/db/session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from services.store import Store

DB_URL = os.getenv("DB_URL", "postgresql+psycopg://dev:dev@localhost:5432/fantasy")

engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(engine, autoflush=False, autocommit=False, future=True)

app = FastAPI(title="FantasyManager Engine", version="1.0.0")

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_store(session: Session = Depends(get_session)):
    return Store(session)

# Example usage in routes:
# def recommend_lineup(..., store: Store = Depends(get_store)):
#     ...
