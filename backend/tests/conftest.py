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
def users_engine() -> Engine:
    """In-memory engine with the users table and no rows."""
    engine = _make_memory_engine()
    _create_users_table(engine)
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
            "quantity_available",
        ]
    ).to_sql("inventory_positions", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=["shipment_id", "delayed_flag", "delay_days"]
    ).to_sql("shipments", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=["maintenance_event_id", "status", "backlog_days"]
    ).to_sql("maintenance_events", engine, if_exists="replace", index=False)


def _create_users_table(engine: Engine) -> None:
    """Create the users table the register_user router writes to."""
    pd.DataFrame(
        columns=["id", "name", "email", "password"]
    ).to_sql("users", engine, if_exists="replace", index=False)


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
                "quantity_available": 10,
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
            "quantity_on_hand",
            "quantity_allocated",
            "quantity_available",
            "reorder_point",
            "safety_stock",
            "stockout_flag",
            "below_reorder_point",
            "below_safety_stock",
            "days_of_supply",
            "snapshot_date",
        ]
    ).to_sql("inventory_positions", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "shipment_id",
            "site_id",
            "part_id",
            "delayed_flag",
            "delay_days",
            "supplier_id",
            "supplier_name",
        ]
    ).to_sql("shipments", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "order_id",
            "order_supplier_name",
            "order_supplier_id",
            "order_part_id",
            "order_quantity",
            "order_status",
            "order_created_at",
            "order_updated_at",
            "site_id",
        ]
    ).to_sql("supplier_orders", engine, if_exists="replace", index=False)
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
    # inventory position ranking (most constrained first).
    for i in range(8):
        is_stockout = i < 5
        qty_avail = 0 if is_stockout else 5
        inv_rows.append({
            "inventory_id": inv_id,
            "site_id": "SITE-A",
            "part_id": f"PART-A{i + 1:03d}",
            "quantity_on_hand": qty_avail + 2,
            "quantity_allocated": 2,
            "quantity_available": qty_avail,
            "reorder_point": 10,
            "safety_stock": 8,
            "stockout_flag": is_stockout,
            "below_reorder_point": True,
            "below_safety_stock": is_stockout,
            "days_of_supply": 0.0 if is_stockout else 12.5,
            "snapshot_date": "2026-01-15",
        })
        inv_id += 1
    # SITE-B: 1 stockout, 2 below_reorder
    for i in range(2):
        is_stockout = i < 1
        qty_avail = 0 if is_stockout else 5
        inv_rows.append({
            "inventory_id": inv_id,
            "site_id": "SITE-B",
            "part_id": f"PART-B{i + 1:03d}",
            "quantity_on_hand": qty_avail + 1,
            "quantity_allocated": 1,
            "quantity_available": qty_avail,
            "reorder_point": 10,
            "safety_stock": 6,
            "stockout_flag": is_stockout,
            "below_reorder_point": True,
            "below_safety_stock": False,
            "days_of_supply": 0.0 if is_stockout else 8.0,
            "snapshot_date": "2026-01-15",
        })
        inv_id += 1
    # SITE-C: 1 row, no issues — exercises the COALESCE/zero path
    inv_rows.append({
        "inventory_id": inv_id,
        "site_id": "SITE-C",
        "part_id": "PART-C001",
        "quantity_on_hand": 110,
        "quantity_allocated": 10,
        "quantity_available": 100,
        "reorder_point": 10,
        "safety_stock": 15,
        "stockout_flag": False,
        "below_reorder_point": False,
        "below_safety_stock": False,
        "days_of_supply": 45.0,
        "snapshot_date": "2026-01-15",
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
            "shipment_id": ship_id,
            "site_id": "SITE-A",
            "part_id": "PART-A001",
            "delayed_flag": True,
            "delay_days": delay,
            "supplier_id": "ACME",
            "supplier_name": "Acme Corp",
        })
        ship_id += 1
    # SITE-B: 2 delayed (delay_days 5 and 5, mean 5.0), 1 on time
    for delayed, delay in [(True, 5), (True, 5), (False, 0)]:
        ship_rows.append({
            "shipment_id": ship_id,
            "site_id": "SITE-B",
            "part_id": "PART-B001",
            "delayed_flag": delayed,
            "delay_days": delay,
            "supplier_id": "BRAVO",
            "supplier_name": "Bravo Supply",
        })
        ship_id += 1
    # SITE-C: 2 on-time shipments, no delays
    for _ in range(2):
        ship_rows.append({
            "shipment_id": ship_id,
            "site_id": "SITE-C",
            "part_id": "PART-C001",
            "delayed_flag": False,
            "delay_days": 0,
            "supplier_id": "CHARLIE",
            "supplier_name": "Charlie Logistics",
        })
        ship_id += 1
    pd.DataFrame(ship_rows).to_sql(
        "shipments", engine, if_exists="replace", index=False
    )
    pd.DataFrame(
        columns=[
            "order_id",
            "order_supplier_name",
            "order_supplier_id",
            "order_part_id",
            "order_quantity",
            "order_status",
            "order_created_at",
            "order_updated_at",
            "site_id",
        ]
    ).to_sql("supplier_orders", engine, if_exists="replace", index=False)

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


def _create_empty_parts_readiness_tables(engine: Engine) -> None:
    """Schema for GET /api/parts/readiness-impact with zero parts.

    All tables referenced in `_PART_READINESS_SQL` must exist so SQLite does
    not raise "no such table" when `part_master` is empty.
    """
    pd.DataFrame(
        columns=["part_id", "part_name", "part_family", "criticality", "nsn"]
    ).to_sql("part_master", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "inventory_id",
            "site_id",
            "part_id",
            "quantity_on_hand",
            "quantity_allocated",
            "quantity_available",
            "reorder_point",
            "safety_stock",
            "stockout_flag",
            "below_reorder_point",
            "below_safety_stock",
            "days_of_supply",
            "snapshot_date",
        ]
    ).to_sql("inventory_positions", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "shipment_id",
            "site_id",
            "part_id",
            "ship_date",
            "expected_delivery_date",
            "actual_delivery_date",
            "quantity_shipped",
            "shipment_status",
            "delayed_flag",
            "delay_days",
        ]
    ).to_sql("shipments", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "maintenance_event_id",
            "site_id",
            "part_id",
            "event_date",
            "equipment_id",
            "status",
            "days_non_mission_capable",
            "backlog_days",
            "defect_flag",
        ]
    ).to_sql("maintenance_events", engine, if_exists="replace", index=False)


def _seed_parts_readiness_impact(engine: Engine) -> None:
    """Deterministic three-part dataset for part readiness ranking tests.

    PART-HOT (High):   4 stockout rows @ SITE-A, 2 open maintenance, 3 delayed
                       shipments — highest raw score -> readiness_risk_score 100.
    PART-MID (Mission Critical): 4 below-reorder rows @ SITE-B, 1 open maint,
                       1 delayed shipment — second rank (~39.6).
    PART-COLD (Low):   no activity — raw 0, score 0.
    """
    pd.DataFrame(
        [
            {
                "part_id": "PART-HOT",
                "part_name": "Hot Part",
                "part_family": "Hydraulics",
                "criticality": "High",
                "nsn": "1-1-1-1",
            },
            {
                "part_id": "PART-MID",
                "part_name": "Mid Part",
                "part_family": "Avionics",
                "criticality": "Mission Critical",
                "nsn": "2-2-2-2",
            },
            {
                "part_id": "PART-COLD",
                "part_name": "Cold Part",
                "part_family": "General",
                "criticality": "Low",
                "nsn": "3-3-3-3",
            },
        ]
    ).to_sql("part_master", engine, if_exists="replace", index=False)

    inv_rows = []
    inv_id = 1
    for _ in range(4):
        inv_rows.append({
            "inventory_id": inv_id,
            "site_id": "SITE-A",
            "part_id": "PART-HOT",
            "quantity_on_hand": 0,
            "quantity_allocated": 0,
            "quantity_available": 0,
            "reorder_point": 100,
            "safety_stock": 50,
            "stockout_flag": True,
            "below_reorder_point": True,
            "below_safety_stock": False,
            "days_of_supply": 0.0,
            "snapshot_date": "2026-01-01",
        })
        inv_id += 1
    for _ in range(4):
        inv_rows.append({
            "inventory_id": inv_id,
            "site_id": "SITE-B",
            "part_id": "PART-MID",
            "quantity_on_hand": 50,
            "quantity_allocated": 40,
            "quantity_available": 10,
            "reorder_point": 100,
            "safety_stock": 50,
            "stockout_flag": False,
            "below_reorder_point": True,
            "below_safety_stock": False,
            "days_of_supply": 2.0,
            "snapshot_date": "2026-01-01",
        })
        inv_id += 1
    pd.DataFrame(inv_rows).to_sql(
        "inventory_positions", engine, if_exists="replace", index=False
    )

    pd.DataFrame(
        [
            {
                "shipment_id": 1,
                "site_id": "SITE-A",
                "part_id": "PART-HOT",
                "ship_date": "2026-01-01",
                "expected_delivery_date": "2026-01-05",
                "actual_delivery_date": "2026-01-08",
                "quantity_shipped": 1,
                "shipment_status": "delivered",
                "delayed_flag": True,
                "delay_days": 3,
            },
            {
                "shipment_id": 2,
                "site_id": "SITE-A",
                "part_id": "PART-HOT",
                "ship_date": "2026-01-02",
                "expected_delivery_date": "2026-01-06",
                "actual_delivery_date": "2026-01-09",
                "quantity_shipped": 1,
                "shipment_status": "delivered",
                "delayed_flag": True,
                "delay_days": 3,
            },
            {
                "shipment_id": 3,
                "site_id": "SITE-A",
                "part_id": "PART-HOT",
                "ship_date": "2026-01-03",
                "expected_delivery_date": "2026-01-07",
                "actual_delivery_date": "2026-01-10",
                "quantity_shipped": 1,
                "shipment_status": "delivered",
                "delayed_flag": True,
                "delay_days": 3,
            },
            {
                "shipment_id": 4,
                "site_id": "SITE-B",
                "part_id": "PART-MID",
                "ship_date": "2026-01-01",
                "expected_delivery_date": "2026-01-05",
                "actual_delivery_date": "2026-01-09",
                "quantity_shipped": 1,
                "shipment_status": "delivered",
                "delayed_flag": True,
                "delay_days": 4,
            },
        ]
    ).to_sql("shipments", engine, if_exists="replace", index=False)

    pd.DataFrame(
        [
            {
                "maintenance_event_id": 1,
                "site_id": "SITE-A",
                "part_id": "PART-HOT",
                "event_date": "2026-01-01",
                "equipment_id": "EQ-1001",
                "status": "open",
                "days_non_mission_capable": 1,
                "backlog_days": 5,
                "defect_flag": False,
            },
            {
                "maintenance_event_id": 2,
                "site_id": "SITE-A",
                "part_id": "PART-HOT",
                "event_date": "2026-01-02",
                "equipment_id": "EQ-1002",
                "status": "open",
                "days_non_mission_capable": 2,
                "backlog_days": 6,
                "defect_flag": False,
            },
            {
                "maintenance_event_id": 3,
                "site_id": "SITE-B",
                "part_id": "PART-MID",
                "event_date": "2026-01-03",
                "equipment_id": "EQ-2001",
                "status": "open",
                "days_non_mission_capable": 1,
                "backlog_days": 3,
                "defect_flag": False,
            },
        ]
    ).to_sql("maintenance_events", engine, if_exists="replace", index=False)


def _create_empty_supplier_risk_tables(engine: Engine) -> None:
    """Tables for GET /api/suppliers/performance with zero rows."""
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
        columns=["part_id", "part_name", "part_family", "criticality"]
    ).to_sql("part_master", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "order_id",
            "order_supplier_name",
            "order_supplier_id",
            "order_part_id",
            "order_quantity",
            "order_status",
            "order_created_at",
            "order_updated_at",
            "site_id",
        ]
    ).to_sql("supplier_orders", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "shipment_id",
            "site_id",
            "part_id",
            "supplier_id",
            "supplier_name",
            "delayed_flag",
            "delay_days",
        ]
    ).to_sql("shipments", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "maintenance_event_id",
            "site_id",
            "part_id",
            "days_non_mission_capable",
            "status",
        ]
    ).to_sql("maintenance_events", engine, if_exists="replace", index=False)


def _seed_supplier_risk_ranking(engine: Engine) -> None:
    """Two suppliers: BAD (many delays / open orders) vs GOOD (clean).

    BAD must rank first (higher performance_risk_score).
    """
    pd.DataFrame(
        [
            {
                "site_id": "SITE-1",
                "site_name": "Alpha Depot",
                "site_region": "North",
                "site_type": "Depot",
                "site_mission_priority": 5,
                "site_active_flag": True,
            },
            {
                "site_id": "SITE-2",
                "site_name": "Bravo Hub",
                "site_region": "South",
                "site_type": "Hub",
                "site_mission_priority": 3,
                "site_active_flag": True,
            },
        ]
    ).to_sql("sites", engine, if_exists="replace", index=False)
    pd.DataFrame(
        [
            {
                "part_id": "PART-A",
                "part_name": "Alpha Component",
                "part_family": "Hydraulics",
                "criticality": "High",
            },
            {
                "part_id": "PART-B",
                "part_name": "Bravo Component",
                "part_family": "Avionics",
                "criticality": "Medium",
            },
        ]
    ).to_sql("part_master", engine, if_exists="replace", index=False)

    order_rows = []
    oid = 1
    for _ in range(20):
        order_rows.append({
            "order_id": oid,
            "order_supplier_name": "BadCorp",
            "order_supplier_id": "BAD",
            "order_part_id": "PART-A",
            "order_quantity": 10,
            "order_status": "pending",
            "order_created_at": "2026-01-01",
            "order_updated_at": "2026-01-02",
            "site_id": "SITE-1",
        })
        oid += 1
    for _ in range(2):
        order_rows.append({
            "order_id": oid,
            "order_supplier_name": "GoodInc",
            "order_supplier_id": "GOOD",
            "order_part_id": "PART-B",
            "order_quantity": 5,
            "order_status": "delivered",
            "order_created_at": "2026-01-01",
            "order_updated_at": "2026-01-05",
            "site_id": "SITE-2",
        })
        oid += 1
    pd.DataFrame(order_rows).to_sql(
        "supplier_orders", engine, if_exists="replace", index=False
    )

    ship_rows = []
    sid = 1
    for i in range(10):
        delayed = i < 8
        ship_rows.append({
            "shipment_id": sid,
            "site_id": "SITE-1",
            "part_id": "PART-A",
            "supplier_id": "BAD",
            "supplier_name": "BadCorp",
            "delayed_flag": delayed,
            "delay_days": 6 if delayed else 0,
        })
        sid += 1
    for _ in range(5):
        ship_rows.append({
            "shipment_id": sid,
            "site_id": "SITE-2",
            "part_id": "PART-B",
            "supplier_id": "GOOD",
            "supplier_name": "GoodInc",
            "delayed_flag": False,
            "delay_days": 0,
        })
        sid += 1
    pd.DataFrame(ship_rows).to_sql(
        "shipments", engine, if_exists="replace", index=False
    )

    pd.DataFrame(
        [
            {
                "maintenance_event_id": 1,
                "site_id": "SITE-1",
                "part_id": "PART-A",
                "days_non_mission_capable": 10,
                "status": "open",
            },
            {
                "maintenance_event_id": 2,
                "site_id": "SITE-1",
                "part_id": "PART-A",
                "days_non_mission_capable": 20,
                "status": "open",
            },
            {
                "maintenance_event_id": 3,
                "site_id": "SITE-2",
                "part_id": "PART-B",
                "days_non_mission_capable": 1,
                "status": "completed",
            },
        ]
    ).to_sql("maintenance_events", engine, if_exists="replace", index=False)


def _create_empty_root_cause_tables(engine: Engine) -> None:
    """Minimal schema for GET /api/root-cause/readiness-risk."""
    pd.DataFrame(columns=["shipment_id", "delayed_flag"]).to_sql(
        "shipments", engine, if_exists="replace", index=False
    )
    pd.DataFrame(
        columns=[
            "order_id",
            "site_id",
            "order_part_id",
            "order_status",
            "order_created_at",
        ]
    ).to_sql("supplier_orders", engine, if_exists="replace", index=False)
    pd.DataFrame(
        columns=[
            "inventory_id",
            "site_id",
            "part_id",
            "below_reorder_point",
            "below_safety_stock",
            "stockout_flag",
            "snapshot_date",
        ]
    ).to_sql("inventory_positions", engine, if_exists="replace", index=False)
    pd.DataFrame(columns=["maintenance_event_id", "status"]).to_sql(
        "maintenance_events", engine, if_exists="replace", index=False
    )


def _seed_root_cause_readiness(engine: Engine) -> None:
    """Deterministic counts: supplier_delay=2, late_site=5 (reactive POs), inventory=4, maint=3."""
    pd.DataFrame(
        [
            {"shipment_id": 1, "delayed_flag": True},
            {"shipment_id": 2, "delayed_flag": True},
            {"shipment_id": 3, "delayed_flag": False},
        ]
    ).to_sql("shipments", engine, if_exists="replace", index=False)

    orders = []
    for i in range(5):
        orders.append({
            "order_id": i + 1,
            "site_id": "SITE-ROOT",
            "order_part_id": "PART-R1",
            "order_status": "pending" if i % 2 == 0 else "delivered",
            "order_created_at": "2026-06-01",
        })
    orders.append({
        "order_id": 6,
        "site_id": "SITE-ROOT",
        "order_part_id": "PART-R1",
        "order_status": "delivered",
        "order_created_at": "2026-01-01",
    })
    pd.DataFrame(orders).to_sql(
        "supplier_orders", engine, if_exists="replace", index=False
    )

    inv = []
    for i in range(4):
        inv.append({
            "inventory_id": i + 1,
            "site_id": "SITE-ROOT",
            "part_id": "PART-R1",
            "below_reorder_point": True,
            "below_safety_stock": False,
            "stockout_flag": False,
            "snapshot_date": "2026-01-01",
        })
    pd.DataFrame(inv).to_sql(
        "inventory_positions", engine, if_exists="replace", index=False
    )

    pd.DataFrame(
        [
            {"maintenance_event_id": 1, "status": "open"},
            {"maintenance_event_id": 2, "status": "in_progress"},
            {"maintenance_event_id": 3, "status": "deferred"},
            {"maintenance_event_id": 4, "status": "completed"},
        ]
    ).to_sql("maintenance_events", engine, if_exists="replace", index=False)


@pytest.fixture
def empty_root_cause_engine() -> Engine:
    """All four tables present with zero rows."""
    engine = _make_memory_engine()
    _create_empty_root_cause_tables(engine)
    return engine


@pytest.fixture
def root_cause_readiness_engine() -> Engine:
    """Seeded for GET /api/root-cause/readiness-risk."""
    engine = _make_memory_engine()
    _seed_root_cause_readiness(engine)
    return engine


@pytest.fixture
def empty_supplier_risk_engine() -> Engine:
    """In-memory DB with supplier ranking schema and no supplier rows."""
    engine = _make_memory_engine()
    _create_empty_supplier_risk_tables(engine)
    return engine


@pytest.fixture
def supplier_risk_engine() -> Engine:
    """In-memory DB seeded for GET /api/suppliers/performance."""
    engine = _make_memory_engine()
    _seed_supplier_risk_ranking(engine)
    return engine


def _seed_orders_only_supplier(engine: Engine) -> None:
    """Supplier with ``supplier_orders`` rows but no ``shipments`` rows."""
    pd.DataFrame(
        [
            {
                "site_id": "SITE-X",
                "site_name": "X Depot",
                "site_region": "West",
                "site_type": "Depot",
                "site_mission_priority": 4,
                "site_active_flag": True,
            },
        ]
    ).to_sql("sites", engine, if_exists="replace", index=False)
    pd.DataFrame(
        [
            {
                "part_id": "PART-X",
                "part_name": "X Component",
                "part_family": "General",
                "criticality": "Medium",
            },
        ]
    ).to_sql("part_master", engine, if_exists="replace", index=False)
    pd.DataFrame(
        [
            {
                "order_id": 1,
                "order_supplier_name": "Orders Only LLC",
                "order_supplier_id": "ORD",
                "order_part_id": "PART-X",
                "order_quantity": 12,
                "order_status": "pending",
                "order_created_at": "2026-01-01",
                "order_updated_at": "2026-01-02",
                "site_id": "SITE-X",
            },
        ]
    ).to_sql("supplier_orders", engine, if_exists="replace", index=False)


@pytest.fixture
def orders_only_supplier_engine() -> Engine:
    """Supplier resolvable from orders only (no shipment history)."""
    engine = _make_memory_engine()
    _create_empty_supplier_risk_tables(engine)
    _seed_orders_only_supplier(engine)
    return engine


@pytest.fixture
def parts_readiness_engine() -> Engine:
    """In-memory DB seeded for GET /api/parts/readiness-impact."""
    engine = _make_memory_engine()
    _seed_parts_readiness_impact(engine)
    return engine


@pytest.fixture
def empty_parts_readiness_engine() -> Engine:
    """Empty `part_master` — endpoint returns zero rows."""
    engine = _make_memory_engine()
    _create_empty_parts_readiness_tables(engine)
    return engine
