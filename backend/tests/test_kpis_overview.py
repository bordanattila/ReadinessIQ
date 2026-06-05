"""Tests for the /api/kpis/overview endpoint.

Uses an in-memory SQLite engine seeded by the `seeded_engine` fixture in
conftest.py. The seeded data is small and deterministic so we can assert on
exact counts and rates.
"""

from __future__ import annotations


def test_overview_returns_status_ok(client_factory, seeded_engine):
    client = client_factory(seeded_engine)

    response = client.get("/api/kpis/overview")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_overview_reports_correct_inventory_metrics(client_factory, seeded_engine):
    # See conftest._seed_inventory: 10 rows, 2 stockouts, 4 below reorder, 1 below safety stock
    client = client_factory(seeded_engine)

    body = client.get("/api/kpis/overview").json()
    inventory = body["inventory"]

    assert inventory["stockout_count"] == 2
    assert inventory["stockout_rate"] == 0.2
    assert inventory["below_reorder_count"] == 4
    assert inventory["below_reorder_rate"] == 0.4


def test_overview_reports_correct_shipment_metrics(client_factory, seeded_engine):
    # See conftest._seed_shipments: 20 rows, 3 delayed with delays 2/4/6 -> mean 4.0
    client = client_factory(seeded_engine)

    shipments = client.get("/api/kpis/overview").json()["shipments"]

    assert shipments["total_shipments"] == 20
    assert shipments["delayed_shipments"] == 3
    assert shipments["delayed_shipment_rate"] == 0.15
    assert shipments["average_delay_days"] == 4.0


def test_overview_reports_correct_maintenance_metrics(client_factory, seeded_engine):
    # See conftest._seed_maintenance: 2 open events with backlog 10/20 -> mean 15.0
    client = client_factory(seeded_engine)

    maintenance = client.get("/api/kpis/overview").json()["maintenance"]

    assert maintenance["open_maintenance_events"] == 2
    assert maintenance["average_backlog_days"] == 15.0


def test_overview_handles_empty_database(client_factory, empty_engine):
    """Zero rows must not blow up averages or rate calculations."""
    client = client_factory(empty_engine)

    body = client.get("/api/kpis/overview").json()

    assert body["status"] == "ok"
    assert body["inventory"]["stockout_rate"] == 0
    assert body["shipments"]["delayed_shipment_rate"] == 0
    # Defensive `or 0` in the router protects against AVG returning NULL
    assert body["shipments"]["average_delay_days"] == 0
    assert body["maintenance"]["average_backlog_days"] == 0
