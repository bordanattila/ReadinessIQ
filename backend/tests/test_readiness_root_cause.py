"""Tests for GET /api/root-cause/readiness-risk."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_readiness_root_cause_empty(empty_root_cause_engine, client_factory):
    client: TestClient = client_factory(empty_root_cause_engine)
    response = client.get("/api/root-cause/readiness-risk")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["scoring_note"] == (
        "relative_severity_score is normalized against the highest root-cause "
        "signal count in the current result set."
    )
    s = body["summary"]
    assert s["primary_root_cause"] == "Insufficient data"
    assert s["total_risk_signals"] == 0
    assert s["supplier_delay_signals"] == 0
    assert s["reactive_site_order_signals"] == 0
    assert s["inventory_policy_signals"] == 0
    assert s["maintenance_demand_signals"] == 0
    assert len(body["root_causes"]) == 4
    for rc in body["root_causes"]:
        assert rc["signal_count"] == 0
        assert rc["share_of_total"] == 0.0
        assert rc["relative_severity_score"] == 0.0
        assert "explanation" in rc and len(rc["explanation"]) > 0


def test_readiness_root_cause_seeded(root_cause_readiness_engine, client_factory):
    client: TestClient = client_factory(root_cause_readiness_engine)
    response = client.get("/api/root-cause/readiness-risk")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["scoring_note"] == (
        "relative_severity_score is normalized against the highest root-cause "
        "signal count in the current result set."
    )
    s = body["summary"]
    assert s["supplier_delay_signals"] == 2
    assert s["reactive_site_order_signals"] == 5
    assert s["inventory_policy_signals"] == 4
    assert s["maintenance_demand_signals"] == 3
    assert s["total_risk_signals"] == 14
    assert s["primary_root_cause"] == "Reactive site ordering"

    by_name = {rc["root_cause"]: rc for rc in body["root_causes"]}
    assert len(by_name) == 4

    late = by_name["Reactive site ordering"]
    assert late["signal_count"] == 5
    assert late["relative_severity_score"] == 100.0
    assert late["share_of_total"] == round(5 / 14, 3)

    inv = by_name["Inventory policy risk"]
    assert inv["signal_count"] == 4
    assert inv["relative_severity_score"] == 80.0
    assert inv["share_of_total"] == round(4 / 14, 3)

    maint = by_name["Maintenance demand"]
    assert maint["signal_count"] == 3
    assert maint["relative_severity_score"] == 60.0

    sup = by_name["Supplier delay"]
    assert sup["signal_count"] == 2
    assert sup["relative_severity_score"] == 40.0

    # Highest signal first
    names = [rc["root_cause"] for rc in body["root_causes"]]
    assert names[0] == "Reactive site ordering"
    assert names[1] == "Inventory policy risk"
