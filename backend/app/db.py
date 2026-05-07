from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from utils.connect_to_db import get_database_url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """FastAPI dependency that returns the SQLAlchemy engine.

    The engine is created lazily on first call and cached. Tests override
    this via `app.dependency_overrides[get_engine]` to point routers at an
    in-memory test database.
    """
    return create_engine(get_database_url())
