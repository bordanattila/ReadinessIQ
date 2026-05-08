"""Tests for GET /api/parts/readiness-impact.

Uses `parts_readiness_engine` / `empty_parts_readiness_engine` from conftest.
See `_seed_parts_readiness_impact` for seeded counts and expected scores.
"""

from __future__ import annotations


def _by_part_id(body: dict) -> dict[str, dict]:
    return {p["part_id"]: p for p in body["parts"]}


def test_readiness_impact_returns_ok(client_factory, parts_readiness_engine):
    client = client_factory(parts_readiness_engine)
    res = client.get("/api/parts/readiness-impact")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_readiness_impact_orders_highest_risk_first(client_factory, parts_readiness_engine):
    client = client_factory(parts_readiness_engine)
    parts = client.get("/api/parts/readiness-impact").json()["parts"]
    assert [p["part_id"] for p in parts][:3] == ["PART-HOT", "PART-MID", "PART-COLD"]


def test_part_hot_is_normalized_to_100(client_factory, parts_readiness_engine):
    client = client_factory(parts_readiness_engine)
    hot = _by_part_id(client.get("/api/parts/readiness-impact").json())["PART-HOT"]
    assert hot["readiness_risk_score"] == 100.0


def test_part_mid_normalized_score_hand_computed(client_factory, parts_readiness_engine):
    """PART-MID raw = 1.4375, max raw (PART-HOT) = 3.63 -> 39.6 after round."""
    client = client_factory(parts_readiness_engine)
    mid = _by_part_id(client.get("/api/parts/readiness-impact").json())["PART-MID"]
    assert mid["readiness_risk_score"] == 39.6


def test_part_cold_has_zero_score(client_factory, parts_readiness_engine):
    client = client_factory(parts_readiness_engine)
    cold = _by_part_id(client.get("/api/parts/readiness-impact").json())["PART-COLD"]
    assert cold["readiness_risk_score"] == 0.0
    assert cold["sites_impacted"] == 0
    assert cold["stockout_count"] == 0
    assert cold["open_maintenance_events"] == 0


def test_part_hot_aggregates_match_seed(client_factory, parts_readiness_engine):
    client = client_factory(parts_readiness_engine)
    hot = _by_part_id(client.get("/api/parts/readiness-impact").json())["PART-HOT"]
    assert hot["part_name"] == "Hot Part"
    assert hot["part_family"] == "Hydraulics"
    assert hot["criticality"] == "High"
    assert hot["sites_impacted"] == 1
    assert hot["stockout_count"] == 4
    assert hot["below_reorder_count"] == 4
    assert hot["total_quantity_available"] == 0
    assert hot["open_maintenance_events"] == 2


def test_part_mid_aggregates_match_seed(client_factory, parts_readiness_engine):
    client = client_factory(parts_readiness_engine)
    mid = _by_part_id(client.get("/api/parts/readiness-impact").json())["PART-MID"]
    assert mid["criticality"] == "Mission Critical"
    assert mid["sites_impacted"] == 1
    assert mid["stockout_count"] == 0
    assert mid["below_reorder_count"] == 4
    assert mid["total_quantity_available"] == 40
    assert mid["open_maintenance_events"] == 1


def test_readiness_impact_no_delayed_shipments_in_payload(client_factory, parts_readiness_engine):
    """Scoring uses delayed counts internally; response must not expose the column."""
    client = client_factory(parts_readiness_engine)
    for p in client.get("/api/parts/readiness-impact").json()["parts"]:
        assert "delayed_shipments" not in p


def test_empty_part_master_returns_empty_list(client_factory, empty_parts_readiness_engine):
    client = client_factory(empty_parts_readiness_engine)
    body = client.get("/api/parts/readiness-impact").json()
    assert body["status"] == "ok"
    assert body["parts"] == []
