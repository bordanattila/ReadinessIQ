"""Unit tests for `app.data_validation.validate_data`.

The validator is pure (DataFrames in, errors out), so these tests build
small in-memory DataFrames covering one rule violation each. A `valid()`
helper builds a fully-valid set we can mutate per test.
"""

from __future__ import annotations

import pandas as pd
import pytest

from app.data_validation import (
    ENUMS,
    FOREIGN_KEYS,
    PRIMARY_KEYS,
    REQUIRED_COLUMNS,
    ValidationError,
    format_errors,
    validate_data,
)


def _valid_tables() -> dict[str, pd.DataFrame]:
    """A minimal but fully-valid set of tables. Tests mutate this per case."""
    return {
        "sites": pd.DataFrame([
            {
                "site_id": "SITE-001", "site_name": "Alpha", "site_region": "N",
                "site_type": "Depot", "site_mission_priority": 5,
                "site_active_flag": True,
            },
            {
                "site_id": "SITE-002", "site_name": "Bravo", "site_region": "S",
                "site_type": "Hub", "site_mission_priority": 3,
                "site_active_flag": True,
            },
        ]),
        "part_master": pd.DataFrame([
            {
                "part_id": "PART-0001", "nsn": "1-2-3-4", "part_name": "Widget",
                "part_family": "Hydraulics", "criticality": "High",
            },
            {
                "part_id": "PART-0002", "nsn": "5-6-7-8", "part_name": "Gizmo",
                "part_family": "Avionics", "criticality": "Medium",
            },
        ]),
        "inventory_positions": pd.DataFrame([
            {
                "inventory_id": 1, "site_id": "SITE-001", "part_id": "PART-0001",
                "quantity_on_hand": 50, "quantity_allocated": 10,
                "quantity_available": 40, "reorder_point": 20, "safety_stock": 10,
                "stockout_flag": False, "below_reorder_point": False,
                "below_safety_stock": False, "days_of_supply": 4.0,
                "snapshot_date": "2026-01-01",
            },
        ]),
        "shipments": pd.DataFrame([
            {
                "shipment_id": 1, "site_id": "SITE-001", "part_id": "PART-0001",
                "ship_date": "2026-01-01", "expected_delivery_date": "2026-01-05",
                "actual_delivery_date": "2026-01-05", "quantity_shipped": 10,
                "shipment_status": "delivered", "delayed_flag": False,
                "delay_days": 0,
            },
        ]),
        "supplier_orders": pd.DataFrame([
            {
                "order_id": 1, "order_supplier_id": "ACME",
                "order_part_id": "PART-0001", "order_quantity": 50,
                "order_status": "shipped", "order_created_at": "2026-01-01",
                "order_updated_at": "2026-01-05",
            },
        ]),
        "maintenance_events": pd.DataFrame([
            {
                "maintenance_event_id": 1, "site_id": "SITE-001",
                "part_id": "PART-0001", "event_date": "2026-01-01",
                "equipment_id": "EQ-1234", "status": "open",
                "days_non_mission_capable": 2, "backlog_days": 5,
                "defect_flag": False,
            },
        ]),
    }


# ---------------------- happy path ----------------------

def test_valid_data_returns_no_errors():
    assert validate_data(_valid_tables()) == []


def test_format_errors_returns_friendly_string_when_no_errors():
    assert format_errors([]) == "No validation errors."


# ---------------------- required columns ----------------------

def test_missing_required_column_is_reported():
    tables = _valid_tables()
    tables["sites"] = tables["sites"].drop(columns=["site_region"])

    errors = validate_data(tables)

    assert any(
        e.table == "sites"
        and e.column == "site_region"
        and "missing required column" in e.message
        for e in errors
    )


def test_extra_columns_are_allowed():
    """Required is a subset, not equality — extras are fine."""
    tables = _valid_tables()
    tables["sites"]["bonus_field"] = "extra"

    assert validate_data(tables) == []


# ---------------------- primary keys ----------------------

def test_duplicate_primary_key_is_reported():
    tables = _valid_tables()
    tables["part_master"] = pd.concat(
        [tables["part_master"], tables["part_master"].iloc[[0]]],
        ignore_index=True,
    )

    errors = validate_data(tables)

    pk_errors = [e for e in errors if e.column == "part_id" and "duplicated" in e.message]
    assert len(pk_errors) == 1
    assert pk_errors[0].table == "part_master"
    assert "PART-0001" in pk_errors[0].message


def test_null_primary_key_is_reported():
    tables = _valid_tables()
    tables["part_master"].loc[0, "part_id"] = None

    errors = validate_data(tables)

    assert any(
        e.table == "part_master"
        and e.column == "part_id"
        and "null" in e.message
        for e in errors
    )


# ---------------------- foreign keys ----------------------

def test_unknown_foreign_key_is_reported():
    tables = _valid_tables()
    tables["inventory_positions"].loc[0, "site_id"] = "SITE-DOES-NOT-EXIST"

    errors = validate_data(tables)

    fk_errors = [
        e for e in errors
        if e.table == "inventory_positions" and e.column == "site_id"
    ]
    assert len(fk_errors) == 1
    assert "SITE-DOES-NOT-EXIST" in fk_errors[0].message
    assert "sites.site_id" in fk_errors[0].message


def test_null_foreign_key_is_reported():
    tables = _valid_tables()
    tables["shipments"].loc[0, "part_id"] = None

    errors = validate_data(tables)

    assert any(
        e.table == "shipments" and e.column == "part_id" and "null" in e.message
        for e in errors
    )


def test_fk_check_skipped_when_parent_table_absent():
    """If parent table itself is missing (e.g. partial upload), don't crash —
    just leave the FK reference check unrun. The parent's own missing-table
    error surfaces through whatever rule the caller cares about elsewhere.
    """
    tables = _valid_tables()
    del tables["sites"]

    errors = validate_data(tables)

    # No error mentions "sites.site_id" because the parent isn't there to check against.
    assert all("sites.site_id" not in e.message for e in errors)


# ---------------------- enum values ----------------------

def test_invalid_enum_value_is_reported():
    tables = _valid_tables()
    tables["part_master"].loc[0, "criticality"] = "Critical"  # not in allowed set

    errors = validate_data(tables)

    enum_errors = [e for e in errors if e.column == "criticality"]
    assert len(enum_errors) == 1
    assert "Critical" in enum_errors[0].message
    assert "High" in enum_errors[0].message  # allowed values mentioned


def test_mission_critical_is_allowed():
    tables = _valid_tables()
    tables["part_master"].loc[0, "criticality"] = "Mission Critical"

    assert validate_data(tables) == []


def test_status_enum_accepts_all_known_values():
    tables = _valid_tables()
    rows = []
    for i, status in enumerate(
        ["open", "in_progress", "awaiting_parts", "completed", "deferred"], start=1
    ):
        rows.append({
            "maintenance_event_id": i, "site_id": "SITE-001",
            "part_id": "PART-0001", "event_date": "2026-01-01",
            "equipment_id": f"EQ-{i}", "status": status,
            "days_non_mission_capable": 1, "backlog_days": 0,
            "defect_flag": False,
        })
    tables["maintenance_events"] = pd.DataFrame(rows)

    assert validate_data(tables) == []


# ---------------------- multiple violations ----------------------

def test_multiple_violations_are_all_returned():
    """Validator never short-circuits — caller wants the full list."""
    tables = _valid_tables()
    tables["sites"] = tables["sites"].drop(columns=["site_region"])
    tables["part_master"].loc[0, "criticality"] = "Critical"
    tables["inventory_positions"].loc[0, "site_id"] = "BOGUS"

    errors = validate_data(tables)

    assert len(errors) >= 3
    error_columns = {e.column for e in errors}
    assert {"site_region", "criticality", "site_id"}.issubset(error_columns)


# ---------------------- partial input ----------------------

def test_empty_input_is_valid():
    """No tables -> nothing to violate. Validator must not crash."""
    assert validate_data({}) == []


def test_partial_input_only_validates_what_was_provided():
    """User uploads only one table -> only its rules run, no FK checks."""
    tables = {
        "part_master": _valid_tables()["part_master"],
    }
    assert validate_data(tables) == []


# ---------------------- schema constants ----------------------

def test_every_foreign_key_points_to_a_known_primary_key():
    """If FOREIGN_KEYS references a parent table, that table must have a PK
    declared in PRIMARY_KEYS — otherwise FK reference checks would silently
    no-op forever."""
    for (_, _), parent_table in FOREIGN_KEYS.items():
        assert parent_table in PRIMARY_KEYS, (
            f"{parent_table} listed as FK target but has no entry in PRIMARY_KEYS"
        )


def test_every_pk_column_is_in_required_columns():
    """A PK that isn't required is a contradiction."""
    for table, pk in PRIMARY_KEYS.items():
        assert pk in REQUIRED_COLUMNS[table], (
            f"PK {pk} not in REQUIRED_COLUMNS[{table}]"
        )


def test_every_enum_column_is_in_required_columns():
    for (table, column), _ in ENUMS.items():
        assert column in REQUIRED_COLUMNS[table], (
            f"enum column {column} not in REQUIRED_COLUMNS[{table}]"
        )
