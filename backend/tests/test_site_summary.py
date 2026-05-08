"""Tests for the /api/sites/{site_id}/summary endpoint.

Reuses `risk_ranking_engine` from conftest.py since both endpoints query the
same set of tables. The fixture seeds three sites with hand-computable
counts; see `_seed_risk_ranking` for the math.
"""

from __future__ import annotations


def test_summary_returns_status_ok(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    response = client.get("/api/sites/SITE-A/summary")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_summary_includes_correct_site_metadata(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    site = client.get("/api/sites/SITE-A/summary").json()["site"]

    assert site == {
        "site_id": "SITE-A",
        "site_name": "Alpha Depot",
        "site_region": "North",
        "site_type": "Depot",
        "mission_priority": 5,
    }


def test_summary_inventory_aggregates(client_factory, risk_ranking_engine):
    # SITE-A has 8 inventory rows, 5 stockouts, 8 below_reorder, 5 below_safety_stock
    client = client_factory(risk_ranking_engine)

    inventory = client.get("/api/sites/SITE-A/summary").json()["inventory"]

    assert inventory == {
        "total_inventory_positions": 8,
        "stockout_count": 5,
        "below_reorder_count": 8,
        "below_safety_stock_count": 5,
    }


def test_summary_shipment_aggregates(client_factory, risk_ranking_engine):
    # SITE-A has 6 delayed shipments with delays 2/3/4/3/3/3 -> mean 3.0
    client = client_factory(risk_ranking_engine)

    shipments = client.get("/api/sites/SITE-A/summary").json()["shipments"]

    assert shipments == {
        "total_shipments": 6,
        "delayed_shipments": 6,
        "delayed_shipment_rate": 1.0,
        "average_delay_days": 3.0,
    }


def test_summary_maintenance_aggregates(client_factory, risk_ranking_engine):
    # SITE-A has 3 open events with backlog 20/30/40 (mean 30); NMC sum = 60.
    client = client_factory(risk_ranking_engine)

    maintenance = client.get("/api/sites/SITE-A/summary").json()["maintenance"]

    assert maintenance == {
        "open_maintenance_events": 3,
        "average_backlog_days": 30.0,
        "total_days_non_mission_capable": 60,
    }


def test_summary_top_constrained_parts_lists_stockouts_first(
    client_factory, risk_ranking_engine
):
    """ORDER BY (quantity_available - reorder_point) ASC puts stockouts first."""
    client = client_factory(risk_ranking_engine)

    top_parts = client.get("/api/sites/SITE-A/summary").json()["top_constrained_parts"]

    assert len(top_parts) == 5
    # All 5 should be stockouts (qty=0, reorder=10 -> diff=-10), and they
    # should come from SITE-A (PART-A001..A005).
    for part in top_parts:
        assert part["quantity_available"] == 0
        assert part["reorder_point"] == 10
        assert part["part_family"] == "Hydraulics"
        assert part["criticality"] == "High"
        assert part["part_id"].startswith("PART-A")


def test_summary_handles_site_with_no_issues(client_factory, risk_ranking_engine):
    # SITE-C: 1 inventory row no issues, 0 delayed shipments, 0 open events.
    client = client_factory(risk_ranking_engine)

    body = client.get("/api/sites/SITE-C/summary").json()

    assert body["status"] == "ok"
    assert body["inventory"]["total_inventory_positions"] == 1
    assert body["inventory"]["stockout_count"] == 0
    # Zero delayed shipments -> AVG returned NULL -> defensive `or 0` kicks in.
    assert body["shipments"]["delayed_shipment_rate"] == 0
    assert body["shipments"]["average_delay_days"] == 0
    assert body["maintenance"]["open_maintenance_events"] == 0
    assert body["maintenance"]["average_backlog_days"] == 0


def test_summary_returns_error_for_unknown_site(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    body = client.get("/api/sites/SITE-DOES-NOT-EXIST/summary").json()

    assert body["status"] == "error"
    assert "not found" in body["message"].lower()


def test_summary_handles_empty_database(client_factory, empty_risk_ranking_engine):
    client = client_factory(empty_risk_ranking_engine)

    body = client.get("/api/sites/SITE-A/summary").json()

    assert body["status"] == "error"
    assert "not found" in body["message"].lower()
