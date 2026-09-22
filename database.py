"""
Database connection setup.
=============================
Why this file exists (separate from models.py and main.py):
Connection logic (engine, session factory) is reused everywhere we
touch the database. Keeping it in one file means every other file
just imports from here instead of repeating connection code.

Which database is used?
  * If the DATABASE_URL environment variable is set  -> PostgreSQL (Neon).
    This is what production (Vercel) uses, so users' accounts, reviews,
    wishlists and saved trips are stored permanently.
  * If DATABASE_URL is NOT set                        -> local SQLite file
    (travel.db), exactly like before. Handy for local development.
"""

import os
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_raw_url = os.environ.get("DATABASE_URL", "").strip()

if _raw_url:
    # ---- PostgreSQL (Neon) ------------------------------------------------
    # SQLAlchemy 2.x needs the "postgresql://" scheme (some providers still
    # hand out the older "postgres://").
    if _raw_url.startswith("postgres://"):
        _raw_url = "postgresql://" + _raw_url[len("postgres://"):]
    DATABASE_URL = _raw_url

    # pool_pre_ping: test a connection before using it (serverless databases
    #   close idle connections, so this avoids "connection closed" errors).
    # pool_recycle: refresh connections every 5 minutes.
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

else:
    # ---- SQLite (local development / emergency fallback) ------------------
    if os.environ.get("VERCEL"):
        # Vercel's project folder is read-only; only /tmp is writable.
        # WARNING: data here is temporary. Set DATABASE_URL for real use.
        print("[database] WARNING: DATABASE_URL is not set - using temporary SQLite in /tmp")
        _src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "travel.db")
        _dst = "/tmp/travel.db"
        if os.path.exists(_src) and not os.path.exists(_dst):
            shutil.copy(_src, _dst)
        DATABASE_URL = "sqlite:////tmp/travel.db"
    else:
        DATABASE_URL = "sqlite:///./travel.db"

    # "check_same_thread=False" is a SQLite-specific setting needed
    # because FastAPI can serve requests from multiple threads.
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal is a factory that creates new database sessions
# (a "session" = one conversation with the database: query, insert, etc.)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class every table model (in models.py) inherits from.
# SQLAlchemy uses it to know which Python classes map to which tables.
Base = declarative_base()


def get_db():
    """
    Dependency function FastAPI will use to hand each request its own
    database session, and guarantee it's closed afterward (even on error).
    We wire this into endpoints in Phase 3+.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()