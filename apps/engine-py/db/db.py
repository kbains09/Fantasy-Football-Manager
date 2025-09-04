import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv("DB_URL", "postgresql+psycopg://dev:dev@postgres:5432/fantasy")

engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
