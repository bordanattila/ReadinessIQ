"""Tests for GET /api/suppliers/performance."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_suppliers_performance_empty(empty_supplier_risk_engine, client_factory):
    client: TestClient = client_factory(empty_supplier_risk_engine)
    response = client.get("/api/suppliers/performance")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["suppliers"] == []


def test_suppliers_performance_bad_supplier_first(supplier_risk_engine, client_factory):
    client: TestClient = client_factory(supplier_risk_engine)
    response = client.get("/api/suppliers/performance")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    suppliers = body["suppliers"]
    assert len(suppliers) == 2
    assert suppliers[0]["supplier_id"] == "BAD"
    assert suppliers[1]["supplier_id"] == "GOOD"
    assert suppliers[0]["performance_risk_score"] >= suppliers[1]["performance_risk_score"]

    bad = suppliers[0]
    assert bad["total_orders"] == 20
    assert bad["open_orders"] == 20
    assert bad["delayed_shipments"] == 8
    assert isinstance(bad["total_orders"], int)
    assert isinstance(bad["sites_supported"], int)
    assert bad["on_time_delivery_rate"] == 0.2
    assert bad["sites_supported"] == 1
    assert bad["parts_supported"] == 1
