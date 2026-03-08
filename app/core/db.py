# app/core/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.base import Base

# 1) DATABASE_URL ni olamiz (env bo'lmasa - hardcode fallback)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://kindergarten:0ha8oxyPXxSe2DCl1efWU27R0YSxIiiG@dpg-d6jcj1s50q8c739ju3m0-a.singapore-postgres.render.com/kindlycloud",
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# 2) engine yaratamiz
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 3) SessionLocal yaratamiz
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4) Model registry: relationship("Pedagogue") kabi stringlar resolve bo‘lishi uchun
import app.models  # noqa: F401


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()