"""Tests for GET /api/parts/{part_id}/summary.

Reuses `risk_ranking_engine` from conftest — same seeded inventory/sites as
the site summary tests.
"""

from __future__ import annotations


def test_part_summary_returns_status_ok(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    response = client.get("/api/parts/PART-A001/summary")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_part_summary_includes_part_metadata(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    part = client.get("/api/parts/PART-A001/summary").json()["part"]

    assert part == {
        "part_id": "PART-A001",
        "part_name": "Alpha Component 1",
        "part_family": "Hydraulics",
        "criticality": "High",
    }


def test_part_summary_inventory_aggregates(client_factory, risk_ranking_engine):
    # PART-A001 exists once at SITE-A as a stockout / below-reorder row.
    client = client_factory(risk_ranking_engine)

    inventory = client.get("/api/parts/PART-A001/summary").json()["inventory"]

    assert inventory == {
        "stockout_count": 1,
        "below_reorder_count": 1,
        "below_safety_stock_count": 1,
    }


def test_part_summary_includes_primary_supplier(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    supplier = client.get("/api/parts/PART-A001/summary").json()["supplier"]

    assert supplier == {
        "supplier_id": "ACME",
        "supplier_name": "Acme Corp",
    }
    assert set(supplier.keys()) == {"supplier_id", "supplier_name"}


def test_part_summary_supplier_null_when_no_supplier_activity(
    client_factory, risk_ranking_engine
):
    client = client_factory(risk_ranking_engine)

    body = client.get("/api/parts/PART-A002/summary").json()

    assert body["status"] == "ok"
    assert body["supplier"] is None


def test_part_summary_lists_impacted_sites(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    sites = client.get("/api/parts/PART-A001/summary").json()["sites_impacted"]

    assert sites == [
        {
            "site_id": "SITE-A",
            "site_name": "Alpha Depot",
            "site_region": "North",
            "site_type": "Depot",
            "mission_priority": 5,
        }
    ]


def test_part_summary_empty_sites_when_no_distress(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    sites = client.get("/api/parts/PART-C001/summary").json()["sites_impacted"]

    assert sites == []


def test_part_summary_shipment_aggregates(client_factory, risk_ranking_engine):
    # PART-A001: 6 SITE-A shipments, all delayed; delays 2/3/4/3/3/3 -> mean 3.0
    client = client_factory(risk_ranking_engine)

    shipments = client.get("/api/parts/PART-A001/summary").json()["shipments"]

    assert shipments == {
        "total_shipments": 6,
        "delayed_shipments": 6,
        "delayed_shipment_rate": 1.0,
        "average_delay_days": 3.0,
    }


def test_part_summary_handles_part_with_no_shipments(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)
    body = client.get("/api/parts/PART-A002/summary").json()

    assert body["status"] == "ok"
    assert body["shipments"] == {
        "total_shipments": 0,
        "delayed_shipments": 0,
        "delayed_shipment_rate": 0,
        "average_delay_days": 0,
    }


def test_part_summary_response_shape(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)
    body = client.get("/api/parts/PART-A001/summary").json()

    assert set(body.keys()) == {
        "status",
        "part",
        "supplier",
        "inventory",
        "shipments",
        "sites_impacted",
    }


def test_part_summary_returns_error_for_unknown_part(
    client_factory, risk_ranking_engine
):
    client = client_factory(risk_ranking_engine)

    body = client.get("/api/parts/PART-DOES-NOT-EXIST/summary").json()

    assert body["status"] == "error"
    assert "not found" in body["message"].lower()


def test_part_summary_handles_empty_database(
    client_factory, empty_risk_ranking_engine
):
    client = client_factory(empty_risk_ranking_engine)

    body = client.get("/api/parts/PART-A001/summary").json()

    assert body["status"] == "error"
    assert "not found" in body["message"].lower()
