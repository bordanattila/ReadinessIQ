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
def risk_ranking_engine() -> Engine:
    """In-memory engine seeded for the /api/sites/risk-ranking endpoint.

    Three sites with hand-computed counts so tests can assert on the exact
    ranking order and normalized scores. See _seed_risk_ranking() below.
    """
    engine = _make_memory_engine()
    _seed_risk_ranking(engine)
    return engine


@pytest.fixture
def empty_risk_ranking_engine() -> Engine:
    """In-memory engine with the risk-ranking schema but zero rows."""
    engine = _make_memory_engine()
    _create_empty_risk_ranking_tables(engine)
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


def _create_empty_risk_ranking_tables(engine: Engine) -> None:
    """Schema for /api/sites/risk-ranking and /api/sites/{id}/summary with zero rows."""
    pd.DataFrame(
        columns=[
            "site_id",
            "site_name",
            "site_region",
            "site_type",
            "site_mission_priority",
            "site_active_flag",
        ]
    ).to_sql("sites", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "inventory_id",
            "site_id",
            "part_id",
            "stockout_flag",
            "below_reorder_point",
            "below_safety_stock",
            "quantity_available",
            "reorder_point",
        ]
    ).to_sql("inventory_positions", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=["shipment_id", "site_id", "delayed_flag", "delay_days"]
    ).to_sql("shipments", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "maintenance_event_id",
            "site_id",
            "status",
            "backlog_days",
            "days_non_mission_capable",
        ]
    ).to_sql("maintenance_events", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=["part_id", "part_name", "part_family", "criticality"]
    ).to_sql("part_master", engine, if_exists="replace", index=False)


def _seed_risk_ranking(engine: Engine) -> None:
    """Three-site fixture with hand-computable risk scores.

    Raw weighted sums (weights: stockout 0.30, below_reorder 0.20,
    delayed 0.20, avg_backlog 0.20, mission_priority 0.10):

      SITE-A: 5*.30 + 8*.20 + 6*.20 + 30*.20 + 5*.10 = 10.80   (rank 1)
      SITE-B: 1*.30 + 2*.20 + 2*.20 + 10*.20 + 3*.10 =  3.40   (rank 2)
      SITE-C: 0    + 0    + 0    + 0    + 1*.10     =  0.10   (rank 3)

    Normalized to 0-100 by max:
      SITE-A -> 100.0,  SITE-B -> 31.5,  SITE-C -> 0.9
    """
    pd.DataFrame(
        [
            {
                "site_id": "SITE-A",
                "site_name": "Alpha Depot",
                "site_region": "North",
                "site_type": "Depot",
                "site_mission_priority": 5,
                "site_active_flag": True,
            },
            {
                "site_id": "SITE-B",
                "site_name": "Bravo Hub",
                "site_region": "South",
                "site_type": "Hub",
                "site_mission_priority": 3,
                "site_active_flag": True,
            },
            {
                "site_id": "SITE-C",
                "site_name": "Charlie Outpost",
                "site_region": "East",
                "site_type": "Outpost",
                "site_mission_priority": 1,
                "site_active_flag": True,
            },
        ]
    ).to_sql("sites", engine, if_exists="replace", index=False)

    inv_rows = []
    inv_id = 1
    # SITE-A: 8 inventory rows. First 5 are stockouts (qty_available=0,
    # reorder=10 -> diff=-10), next 3 are below_reorder (qty=5, reorder=10 ->
    # diff=-5). All 8 are "below_reorder_point". Stockouts will dominate the
    # "top constrained parts" ranking.
    for i in range(8):
        is_stockout = i < 5
        inv_rows.append({
            "inventory_id": inv_id,
            "site_id": "SITE-A",
            "part_id": f"PART-A{i + 1:03d}",
            "stockout_flag": is_stockout,
            "below_reorder_point": True,
            "below_safety_stock": is_stockout,
            "quantity_available": 0 if is_stockout else 5,
            "reorder_point": 10,
        })
        inv_id += 1
    # SITE-B: 1 stockout, 2 below_reorder
    for i in range(2):
        is_stockout = i < 1
        inv_rows.append({
            "inventory_id": inv_id,
            "site_id": "SITE-B",
            "part_id": f"PART-B{i + 1:03d}",
            "stockout_flag": is_stockout,
            "below_reorder_point": True,
            "below_safety_stock": False,
            "quantity_available": 0 if is_stockout else 5,
            "reorder_point": 10,
        })
        inv_id += 1
    # SITE-C: 1 row, no issues — exercises the COALESCE/zero path
    inv_rows.append({
        "inventory_id": inv_id,
        "site_id": "SITE-C",
        "part_id": "PART-C001",
        "stockout_flag": False,
        "below_reorder_point": False,
        "below_safety_stock": False,
        "quantity_available": 100,
        "reorder_point": 10,
    })
    pd.DataFrame(inv_rows).to_sql(
        "inventory_positions", engine, if_exists="replace", index=False
    )

    # part_master rows for every part_id referenced above, so the JOIN in
    # /api/sites/{id}/summary's top-parts query can resolve part metadata.
    part_rows = []
    for i in range(8):
        part_rows.append({
            "part_id": f"PART-A{i + 1:03d}",
            "part_name": f"Alpha Component {i + 1}",
            "part_family": "Hydraulics",
            "criticality": "High",
        })
    for i in range(2):
        part_rows.append({
            "part_id": f"PART-B{i + 1:03d}",
            "part_name": f"Bravo Component {i + 1}",
            "part_family": "Avionics",
            "criticality": "Medium",
        })
    part_rows.append({
        "part_id": "PART-C001",
        "part_name": "Charlie Component 1",
        "part_family": "General",
        "criticality": "Low",
    })
    pd.DataFrame(part_rows).to_sql(
        "part_master", engine, if_exists="replace", index=False
    )

    ship_rows = []
    ship_id = 1
    # SITE-A: 6 delayed (out of 6) with delay_days summing to 18 (mean 3.0)
    site_a_delays = [2, 3, 4, 3, 3, 3]
    for delay in site_a_delays:
        ship_rows.append({
            "shipment_id": ship_id, "site_id": "SITE-A",
            "delayed_flag": True, "delay_days": delay,
        })
        ship_id += 1
    # SITE-B: 2 delayed (delay_days 5 and 5, mean 5.0), 1 on time
    for delayed, delay in [(True, 5), (True, 5), (False, 0)]:
        ship_rows.append({
            "shipment_id": ship_id, "site_id": "SITE-B",
            "delayed_flag": delayed, "delay_days": delay,
        })
        ship_id += 1
    # SITE-C: 2 on-time shipments, no delays
    for _ in range(2):
        ship_rows.append({
            "shipment_id": ship_id, "site_id": "SITE-C",
            "delayed_flag": False, "delay_days": 0,
        })
        ship_id += 1
    pd.DataFrame(ship_rows).to_sql(
        "shipments", engine, if_exists="replace", index=False
    )

    maint_rows = [
        # SITE-A: 3 open events with backlog 20/30/40 (mean 30); NMC days sum = 60.
        {"maintenance_event_id": 1, "site_id": "SITE-A", "status": "open",
         "backlog_days": 20, "days_non_mission_capable": 10},
        {"maintenance_event_id": 2, "site_id": "SITE-A", "status": "open",
         "backlog_days": 30, "days_non_mission_capable": 20},
        {"maintenance_event_id": 3, "site_id": "SITE-A", "status": "open",
         "backlog_days": 40, "days_non_mission_capable": 30},
        # SITE-B: 1 open with backlog 10 (mean 10), 1 completed; NMC sum = 5.
        {"maintenance_event_id": 4, "site_id": "SITE-B", "status": "open",
         "backlog_days": 10, "days_non_mission_capable": 5},
        {"maintenance_event_id": 5, "site_id": "SITE-B", "status": "completed",
         "backlog_days": 0, "days_non_mission_capable": 0},
        # SITE-C: only completed events — exercises avg-backlog COALESCE to 0.
        {"maintenance_event_id": 6, "site_id": "SITE-C", "status": "completed",
         "backlog_days": 0, "days_non_mission_capable": 0},
    ]
    pd.DataFrame(maint_rows).to_sql(
        "maintenance_events", engine, if_exists="replace", index=False
    )
