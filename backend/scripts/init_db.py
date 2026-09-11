"""Create the database schema from the SQLAlchemy models and stamp Alembic.

The Alembic chain in alembic/versions/ is incremental: it assumes a legacy base
schema that was never captured as a migration, so `alembic upgrade head` cannot
build an empty database. For a fresh database we create the schema from the
models (the same thing the test suite does) and then stamp Alembic at head so
future migrations apply normally.

Usage:
    .venv-linux/bin/python scripts/init_db.py          # create missing tables
    .venv-linux/bin/python scripts/init_db.py --drop   # wipe and recreate
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect

from app.core.base import Base
from app.core.db import engine
import app.models  # noqa: F401  - registers every model on Base.metadata
from config import settings


def main() -> None:
    print(f"Database: {settings.DATABASE_URL.rsplit('@', 1)[-1]}")

    if "--drop" in sys.argv:
        print("Dropping every table ...")
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)
    tables = sorted(inspect(engine).get_table_names())
    print(f"Schema ready: {len(tables)} tables")
    print("  " + ", ".join(tables))

    alembic_bin = Path(sys.executable).with_name("alembic")
    subprocess.run([str(alembic_bin), "stamp", "head"], cwd=ROOT, check=True)
    print("Alembic stamped at head.")


if __name__ == "__main__":
    main()
