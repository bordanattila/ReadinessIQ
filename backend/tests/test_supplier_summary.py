"""Tests for GET /api/suppliers/{supplier_id}/summary."""

from __future__ import annotations


def test_supplier_summary_returns_status_ok(client_factory, supplier_risk_engine):
    client = client_factory(supplier_risk_engine)

    response = client.get("/api/suppliers/BAD/summary")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_supplier_summary_includes_supplier_metadata(
    client_factory, supplier_risk_engine
):
    client = client_factory(supplier_risk_engine)

    supplier = client.get("/api/suppliers/BAD/summary").json()["supplier"]

    assert supplier == {
        "supplier_id": "BAD",
        "supplier_name": "BadCorp",
    }
    assert set(supplier.keys()) == {"supplier_id", "supplier_name"}


def test_supplier_summary_orders_and_shipments(client_factory, supplier_risk_engine):
    client = client_factory(supplier_risk_engine)
    body = client.get("/api/suppliers/BAD/summary").json()

    assert body["orders"] == {
        "total_orders": 20,
        "open_orders": 20,
    }
    assert body["shipments"] == {
        "total_shipments": 10,
        "delayed_shipments": 8,
        "delayed_shipment_rate": 0.8,
        "average_delay_days": 6.0,
    }


def test_supplier_summary_parts_and_sites(client_factory, supplier_risk_engine):
    client = client_factory(supplier_risk_engine)
    body = client.get("/api/suppliers/BAD/summary").json()

    assert body["parts_supplied"] == [
        {
            "part_id": "PART-A",
            "part_name": "Alpha Component",
            "part_family": "Hydraulics",
            "criticality": "High",
        }
    ]
    assert body["sites_supported"] == [
        {
            "site_id": "SITE-1",
            "site_name": "Alpha Depot",
            "site_region": "North",
            "site_type": "Depot",
            "mission_priority": 5,
        }
    ]


def test_supplier_summary_good_supplier_metrics(client_factory, supplier_risk_engine):
    client = client_factory(supplier_risk_engine)
    body = client.get("/api/suppliers/GOOD/summary").json()

    assert body["status"] == "ok"
    assert body["supplier"] == {
        "supplier_id": "GOOD",
        "supplier_name": "GoodInc",
    }
    assert body["orders"] == {
        "total_orders": 2,
        "open_orders": 0,
    }
    assert body["shipments"] == {
        "total_shipments": 5,
        "delayed_shipments": 0,
        "delayed_shipment_rate": 0,
        "average_delay_days": 0,
    }


def test_supplier_summary_resolves_supplier_from_orders_only(
    client_factory, orders_only_supplier_engine
):
    client = client_factory(orders_only_supplier_engine)
    body = client.get("/api/suppliers/ORD/summary").json()

    assert body["status"] == "ok"
    assert body["supplier"] == {
        "supplier_id": "ORD",
        "supplier_name": "Orders Only LLC",
    }
    assert body["orders"] == {"total_orders": 1, "open_orders": 1}
    assert body["shipments"] == {
        "total_shipments": 0,
        "delayed_shipments": 0,
        "delayed_shipment_rate": 0,
        "average_delay_days": 0,
    }
    assert body["parts_supplied"] == [
        {
            "part_id": "PART-X",
            "part_name": "X Component",
            "part_family": "General",
            "criticality": "Medium",
        }
    ]
    assert body["sites_supported"] == [
        {
            "site_id": "SITE-X",
            "site_name": "X Depot",
            "site_region": "West",
            "site_type": "Depot",
            "mission_priority": 4,
        }
    ]


def test_supplier_summary_response_shape(client_factory, supplier_risk_engine):
    client = client_factory(supplier_risk_engine)
    body = client.get("/api/suppliers/BAD/summary").json()

    assert set(body.keys()) == {
        "status",
        "supplier",
        "parts_supplied",
        "sites_supported",
        "orders",
        "shipments",
    }


def test_supplier_summary_returns_error_for_unknown_supplier(
    client_factory, supplier_risk_engine
):
    client = client_factory(supplier_risk_engine)

    body = client.get("/api/suppliers/UNKNOWN/summary").json()

    assert body["status"] == "error"
    assert "not found" in body["message"].lower()


def test_supplier_summary_handles_empty_database(
    client_factory, empty_supplier_risk_engine
):
    client = client_factory(empty_supplier_risk_engine)

    body = client.get("/api/suppliers/BAD/summary").json()

    assert body["status"] == "error"
    assert "not found" in body["message"].lower()
