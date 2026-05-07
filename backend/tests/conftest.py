"""Shared fixtures for the ReadinessIQ test suite.

The TestClient fixture overrides `app.db.get_engine` so the API routers run
against an in-memory SQLite database that we seed per-test. This keeps the
tests fast (<1s for the whole suite) and removes the need for a running
Postgres instance.
"""

from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from app.db import get_engine
from app.main import app


def _make_memory_engine() -> Engine:
    """Build an in-memory SQLite engine that's safe to share across connections.

    `StaticPool` reuses a single underlying connection for the lifetime of the
    engine. Without it, each `engine.connect()` call would see a fresh empty
    database (SQLite gives every connection its own `:memory:` instance).
    """
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def empty_engine() -> Engine:
    """An in-memory SQLite engine with the project's tables but no rows."""
    engine = _make_memory_engine()
    _create_empty_tables(engine)
    return engine


@pytest.fixture
def seeded_engine() -> Engine:
    """An in-memory SQLite engine populated with deterministic test data."""
    engine = _make_memory_engine()
    _seed_inventory(engine)
    _seed_shipments(engine)
    _seed_maintenance(engine)
    return engine


@pytest.fixture
def client_factory():
    """Returns a function that builds a TestClient bound to a given engine."""

    def _build(engine: Engine) -> TestClient:
        app.dependency_overrides[get_engine] = lambda: engine
        return TestClient(app)

    yield _build
    app.dependency_overrides.clear()


def _create_empty_tables(engine: Engine) -> None:
    """Create the tables the routers query against, with zero rows."""
    pd.DataFrame(
        columns=[
            "inventory_id",
            "stockout_flag",
            "below_reorder_point",
            "below_safety_stock",
        ]
    ).to_sql("inventory_positions", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=["shipment_id", "delayed_flag", "delay_days"]
    ).to_sql("shipments", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=["maintenance_event_id", "status", "backlog_days"]
    ).to_sql("maintenance_events", engine, if_exists="replace", index=False)


def _seed_inventory(engine: Engine) -> None:
    # 10 rows: 2 stockouts, 4 below reorder point, 1 below safety stock
    rows = []
    for i in range(10):
        rows.append(
            {
                "inventory_id": i + 1,
                "stockout_flag": i < 2,
                "below_reorder_point": i < 4,
                "below_safety_stock": i < 1,
            }
        )
    pd.DataFrame(rows).to_sql(
        "inventory_positions", engine, if_exists="replace", index=False
    )


def _seed_shipments(engine: Engine) -> None:
    # 20 rows, 3 delayed with delays 2/4/6 days -> mean 4.0
    rows = []
    for i in range(20):
        delayed = i < 3
        rows.append(
            {
                "shipment_id": i + 1,
                "delayed_flag": delayed,
                "delay_days": [2, 4, 6][i] if delayed else 0,
            }
        )
    pd.DataFrame(rows).to_sql(
        "shipments", engine, if_exists="replace", index=False
    )


def _seed_maintenance(engine: Engine) -> None:
    # 5 events: 2 open with backlog 10/20 (mean 15.0), 3 completed
    rows = [
        {"maintenance_event_id": 1, "status": "open", "backlog_days": 10},
        {"maintenance_event_id": 2, "status": "open", "backlog_days": 20},
        {"maintenance_event_id": 3, "status": "completed", "backlog_days": 0},
        {"maintenance_event_id": 4, "status": "completed", "backlog_days": 0},
        {"maintenance_event_id": 5, "status": "in_progress", "backlog_days": 5},
    ]
    pd.DataFrame(rows).to_sql(
        "maintenance_events", engine, if_exists="replace", index=False
    )
