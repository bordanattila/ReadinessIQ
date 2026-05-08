"""Tests for the /api/sites/risk-ranking endpoint.

The `risk_ranking_engine` fixture in conftest.py seeds three sites
(SITE-A, SITE-B, SITE-C) with counts chosen so the raw weighted score and
the 0-100 normalized score are hand-computable. See
`_seed_risk_ranking` for the math.
"""

from __future__ import annotations


def _sites_by_id(body: dict) -> dict[str, dict]:
    return {site["site_id"]: site for site in body["sites"]}


def test_risk_ranking_returns_status_ok(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    response = client.get("/api/sites/risk-ranking")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_risk_ranking_returns_one_row_per_site(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    body = client.get("/api/sites/risk-ranking").json()

    assert len(body["sites"]) == 3
    assert {s["site_id"] for s in body["sites"]} == {"SITE-A", "SITE-B", "SITE-C"}


def test_risk_ranking_orders_by_score_descending(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    sites = client.get("/api/sites/risk-ranking").json()["sites"]

    site_ids = [s["site_id"] for s in sites]
    assert site_ids == ["SITE-A", "SITE-B", "SITE-C"]

    scores = [s["readiness_risk_score"] for s in sites]
    assert scores == sorted(scores, reverse=True)


def test_top_site_score_is_normalized_to_100(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    sites = client.get("/api/sites/risk-ranking").json()["sites"]

    assert sites[0]["readiness_risk_score"] == 100.0


def test_aggregates_match_seeded_counts(client_factory, risk_ranking_engine):
    client = client_factory(risk_ranking_engine)

    by_id = _sites_by_id(client.get("/api/sites/risk-ranking").json())

    assert by_id["SITE-A"]["stockout_count"] == 5
    assert by_id["SITE-A"]["below_reorder_count"] == 8
    assert by_id["SITE-A"]["delayed_shipments"] == 6
    assert by_id["SITE-A"]["open_maintenance_events"] == 3
    assert by_id["SITE-A"]["avg_backlog_days"] == 30.0

    assert by_id["SITE-B"]["stockout_count"] == 1
    assert by_id["SITE-B"]["below_reorder_count"] == 2
    assert by_id["SITE-B"]["delayed_shipments"] == 2
    assert by_id["SITE-B"]["open_maintenance_events"] == 1
    assert by_id["SITE-B"]["avg_backlog_days"] == 10.0

    # SITE-C has zero issues but still appears (LEFT JOIN + COALESCE)
    assert by_id["SITE-C"]["stockout_count"] == 0
    assert by_id["SITE-C"]["below_reorder_count"] == 0
    assert by_id["SITE-C"]["delayed_shipments"] == 0
    assert by_id["SITE-C"]["open_maintenance_events"] == 0
    assert by_id["SITE-C"]["avg_backlog_days"] == 0.0


def test_normalized_scores_match_hand_computation(client_factory, risk_ranking_engine):
    """Lock down the exact normalized score values.

    Raw scores per `_seed_risk_ranking`: SITE-A=10.80, SITE-B=3.40, SITE-C=0.10.
    Normalized = raw / 10.80 * 100 then rounded to 1 decimal.
    """
    client = client_factory(risk_ranking_engine)

    by_id = _sites_by_id(client.get("/api/sites/risk-ranking").json())

    assert by_id["SITE-A"]["readiness_risk_score"] == 100.0
    assert by_id["SITE-B"]["readiness_risk_score"] == 31.5
    assert by_id["SITE-C"]["readiness_risk_score"] == 0.9


def test_response_includes_site_metadata(client_factory, risk_ranking_engine):
    """Each site row carries through the descriptive columns from `sites`."""
    client = client_factory(risk_ranking_engine)

    by_id = _sites_by_id(client.get("/api/sites/risk-ranking").json())

    assert by_id["SITE-A"]["site_name"] == "Alpha Depot"
    assert by_id["SITE-A"]["site_region"] == "North"
    assert by_id["SITE-A"]["site_type"] == "Depot"
    assert by_id["SITE-A"]["mission_priority"] == 5


def test_handles_empty_database(client_factory, empty_risk_ranking_engine):
    """No sites -> empty list, never an error."""
    client = client_factory(empty_risk_ranking_engine)

    body = client.get("/api/sites/risk-ranking").json()

    assert body["status"] == "ok"
    assert body["sites"] == []
