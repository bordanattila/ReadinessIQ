"""Unit tests for the synthetic data generators.

These tests lock down the shape and key statistical properties of the
generated data, so changes to the generators that break downstream
consumers (the loader, the KPI endpoint) fail fast.
"""

from __future__ import annotations

import datetime
import random

import pytest

import generate_synthetic_data as gsd


@pytest.fixture(autouse=True)
def deterministic_random():
    """Seed `random` so each test runs against the same synthetic dataset."""
    random.seed(0)
    yield


# ---------- get_random_date ----------

def test_get_random_date_returns_a_date_in_range():
    d = gsd.get_random_date(start_year=2024)

    assert isinstance(d, datetime.date)
    assert 2024 <= d.year <= 2026
    assert 1 <= d.month <= 12
    assert 1 <= d.day <= 28


# ---------- _generate_supplier_id ----------

def test_supplier_id_is_uppercase_initials():
    assert gsd._generate_supplier_id("Lockheed Martin Aerospace") == "LMA"
    assert gsd._generate_supplier_id("Acme") == "A"
    assert gsd._generate_supplier_id("all lowercase") == ""


# ---------- generate_sites_data ----------

def test_sites_dataframe_has_expected_columns():
    df = gsd.generate_sites_data()

    expected = {
        "site_id",
        "site_name",
        "site_region",
        "site_type",
        "site_mission_priority",
        "site_active_flag",
    }
    assert expected.issubset(df.columns)
    assert len(df) > 0


# ---------- generate_part_master_data ----------

def test_parts_dataframe_has_expected_columns():
    df = gsd.generate_part_master_data()

    expected = {"part_id", "nsn", "part_name", "part_family", "criticality"}
    assert expected.issubset(df.columns)
    assert len(df) > 0


# ---------- generate_inventory_positions_data ----------

def test_inventory_positions_invariants():
    sites = gsd.generate_sites_data()
    parts = gsd.generate_part_master_data()

    df = gsd.generate_inventory_positions_data(
        sites_df=sites, parts_df=parts, num_positions=200
    )

    assert len(df) == 200
    # Each row's available = on_hand - allocated
    assert (
        df["quantity_available"]
        == df["quantity_on_hand"] - df["quantity_allocated"]
    ).all()
    # stockout_flag must agree with quantity_available == 0
    assert (df["stockout_flag"] == (df["quantity_available"] == 0)).all()
    # below_reorder_point implies below_safety_stock can be true or false,
    # but below_safety_stock must always imply below_reorder_point
    below_safety_only = df[df["below_safety_stock"] & ~df["below_reorder_point"]]
    assert len(below_safety_only) == 0


# ---------- generate_shipments_data ----------

def test_shipments_delay_rate_is_realistic():
    """The generator targets ~12% delays. Allow a wide tolerance band so
    this doesn't flake under different RNG seeds in the future.
    """
    sites = gsd.generate_sites_data()
    parts = gsd.generate_part_master_data()

    df = gsd.generate_shipments_data(sites_df=sites, parts_df=parts, num_shipments=2000)

    delay_rate = df["delayed_flag"].mean()
    assert 0.05 < delay_rate < 0.20, f"delay rate {delay_rate:.3f} outside realistic band"


def test_shipments_delay_days_consistency():
    sites = gsd.generate_sites_data()
    parts = gsd.generate_part_master_data()

    df = gsd.generate_shipments_data(sites_df=sites, parts_df=parts, num_shipments=500)

    # delayed_flag must agree with actual > expected
    actual_after_expected = df["actual_delivery_date"] > df["expected_delivery_date"]
    assert (df["delayed_flag"] == actual_after_expected).all()

    # delay_days must be 0 for non-delayed shipments and >=1 for delayed ones
    assert (df.loc[~df["delayed_flag"], "delay_days"] == 0).all()
    assert (df.loc[df["delayed_flag"], "delay_days"] >= 1).all()


# ---------- generate_maintenance_events_data ----------

def test_maintenance_events_completed_have_zero_backlog():
    sites = gsd.generate_sites_data()
    parts = gsd.generate_part_master_data()

    df = gsd.generate_maintenance_events_data(
        sites_df=sites, parts_df=parts, num_events=500
    )

    assert (df.loc[df["status"] == "completed", "backlog_days"] == 0).all()
    assert df["status"].isin(
        ["open", "in_progress", "awaiting_parts", "completed", "deferred"]
    ).all()


# ---------- generate_supplier_orders_data ----------

def test_supplier_orders_has_expected_columns():
    sites = gsd.generate_sites_data()
    parts = gsd.generate_part_master_data()
    df = gsd.generate_supplier_orders_data(
        sites_df=sites, parts_df=parts, num_orders=100
    )

    expected = {
        "order_id",
        "order_supplier_name",
        "order_supplier_id",
        "order_part_id",
        "order_quantity",
        "order_status",
        "order_created_at",
        "order_updated_at",
        "site_id",
    }
    assert expected.issubset(df.columns)
    assert len(df) == 100
    assert df["order_part_id"].isin(parts["part_id"]).all()
    assert df["site_id"].isin(sites["site_id"]).all()
    # updated_at should be on or after created_at
    assert (df["order_updated_at"] >= df["order_created_at"]).all()
