# app/core/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.base import Base
from config import settings

DATABASE_URL = settings.DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

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
