from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ami.models import Base

DB_PATH = Path.home() / ".ami" / "ami.sqlite"

SessionFactory: sessionmaker | None = None

_session: Session | None = None


def init_db() -> Session:
    """Create the DB directory, run create_all, and return the singleton Session."""
    global _session, SessionFactory

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)

    if _session is None:
        SessionFactory = sessionmaker(bind=engine)
        _session = SessionFactory()

    return _session


def get_session() -> Session:
    """Return the singleton Session. Raises RuntimeError if init_db() has not been called."""
    if _session is None:
        raise RuntimeError(
            "Database session has not been initialized. Call init_db() first."
        )
    return _session
