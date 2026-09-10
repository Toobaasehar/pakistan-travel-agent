"""
Database connection setup.
=============================
Why this file exists (separate from models.py and main.py):
Connection logic (engine, session factory) is reused everywhere we
touch the database. Keeping it in one file means every other file
just imports from here instead of repeating connection code.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite file will be created automatically in this same folder.
# "check_same_thread=False" is a SQLite-specific setting needed
# because FastAPI can serve requests from multiple threads.
DATABASE_URL = "sqlite:///./travel.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

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
