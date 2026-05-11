"""Validation rules for the project's tabular data.

The validator is a pure function: DataFrames in, structured errors out. No
I/O, no DB. Three callers compose it with their own data sources:

  1. `load_csv_to_postgres.py`        — read CSVs, validate, insert.
  2. `generate_synthetic_data.py`     — generate, validate, write CSVs.
  3. (future) the user-upload route   — parse upload, validate, insert.

Schema constants (REQUIRED_COLUMNS, PRIMARY_KEYS, FOREIGN_KEYS, ENUMS) live
here so the validator and its callers always agree on the rules.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


# ---------------------------------------------------------------------------
# Schema constants — single source of truth for what each table must contain.
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS: dict[str, set[str]] = {
    'sites': {
        'site_id',
        'site_name',
        'site_region',
        'site_type',
        'site_mission_priority',
        'site_active_flag',
    },
    'part_master': {
        'part_id',
        'nsn',
        'part_name',
        'part_family',
        'criticality',
    },
    'inventory_positions': {
        'inventory_id',
        'site_id',
        'part_id',
        'quantity_on_hand',
        'quantity_allocated',
        'quantity_available',
        'reorder_point',
        'safety_stock',
        'stockout_flag',
        'below_reorder_point',
        'below_safety_stock',
        'days_of_supply',
        'snapshot_date',
    },
    'shipments': {
        'shipment_id',
        'site_id',
        'part_id',
        'ship_date',
        'expected_delivery_date',
        'actual_delivery_date',
        'quantity_shipped',
        'shipment_status',
        'delayed_flag',
        'delay_days',
        'supplier_id',
        'supplier_name',
    },
    'supplier_orders': {
        'order_id',
        'order_supplier_name',
        'order_supplier_id',
        'order_part_id',
        'order_quantity',
        'order_status',
        'order_created_at',
        'order_updated_at',
        'site_id',
    },
    'maintenance_events': {
        'maintenance_event_id',
        'site_id',
        'part_id',
        'event_date',
        'equipment_id',
        'status',
        'days_non_mission_capable',
        'backlog_days',
        'defect_flag',
    },
}

PRIMARY_KEYS: dict[str, str] = {
    'sites':                'site_id',
    'part_master':          'part_id',
    'inventory_positions':  'inventory_id',
    'shipments':            'shipment_id',
    'maintenance_events':   'maintenance_event_id',
    'supplier_orders':      'order_id',
}

# (table, column) -> the parent table whose primary key must contain the value.
FOREIGN_KEYS: dict[tuple[str, str], str] = {
    ('inventory_positions', 'site_id'): 'sites',
    ('inventory_positions', 'part_id'): 'part_master',
    ('shipments',           'site_id'): 'sites',
    ('shipments',           'part_id'): 'part_master',
    ('maintenance_events',  'site_id'): 'sites',
    ('maintenance_events',  'part_id'): 'part_master',
    ('supplier_orders', 'order_part_id'): 'part_master',
    ('supplier_orders', 'site_id'): 'sites',
}

# (table, column) -> set of allowed values.
ENUMS: dict[tuple[str, str], set[str]] = {
    # Parts master source data uses four tiers; keep aligned with
    # `data_generator_support_files/generate_parts_master_1000.py`.
    ('part_master',        'criticality'): {
        'High', 'Medium', 'Low', 'Mission Critical',
    },
    ('maintenance_events', 'status'):      {
        'open', 'in_progress', 'awaiting_parts', 'completed', 'deferred',
    },
}


@dataclass(frozen=True)
class ValidationError:
    """A single rule violation. `column` is None for table-level errors."""
    table: str
    column: str | None
    message: str


def validate_data(tables: dict[str, pd.DataFrame]) -> list[ValidationError]:
    """Return all rule violations across all tables; empty list = valid.

    The function never raises on bad data — it collects every violation so
    the caller can show users a complete report. It only raises if it
    receives something other than a `dict[str, pd.DataFrame]`.

    Checks run in this order so each one can rely on the previous passing:
      1. Required columns present.
      2. Primary keys: not null, unique.
      3. Foreign keys: not null, every value exists in the parent table.
      4. Enum columns: every value is in the allowed set.
    """
    errors: list[ValidationError] = []

    # 1. Required columns first — every later check assumes its column exists.
    for table_name, df in tables.items():
        required = REQUIRED_COLUMNS.get(table_name)
        if required is None:
            continue
        for column in sorted(required - set(df.columns)):
            errors.append(ValidationError(
                table=table_name,
                column=column,
                message=f"missing required column '{column}'",
            ))

    def _has_column(table_name: str, column: str) -> bool:
        df = tables.get(table_name)
        return df is not None and column in df.columns

    # 2. Primary keys: non-null + unique.
    for table_name, pk in PRIMARY_KEYS.items():
        if not _has_column(table_name, pk):
            continue
        df = tables[table_name]

        if df[pk].isnull().any():
            errors.append(ValidationError(
                table=table_name,
                column=pk,
                message=f"primary key '{pk}' contains null values",
            ))

        duplicate_values = df[pk][df[pk].duplicated(keep=False)]
        if not duplicate_values.empty:
            sample = list(duplicate_values.unique()[:5])
            errors.append(ValidationError(
                table=table_name,
                column=pk,
                message=(
                    f"primary key '{pk}' has {len(duplicate_values)} duplicated "
                    f"row(s) (e.g. {sample})"
                ),
            ))

    # 3. Foreign keys: non-null + reference exists in parent table.
    for (table_name, fk), parent_table in FOREIGN_KEYS.items():
        if not _has_column(table_name, fk):
            continue
        df = tables[table_name]

        if df[fk].isnull().any():
            errors.append(ValidationError(
                table=table_name,
                column=fk,
                message=f"foreign key '{fk}' contains null values",
            ))

        # Skip the reference check if the parent table or its PK is missing —
        # those are already reported as their own errors above.
        parent_df = tables.get(parent_table)
        parent_pk = PRIMARY_KEYS.get(parent_table)
        if parent_df is None or parent_pk is None or parent_pk not in parent_df.columns:
            continue

        valid_keys = set(parent_df[parent_pk].dropna())
        non_null = df[fk].dropna()
        invalid = non_null[~non_null.isin(valid_keys)]
        if not invalid.empty:
            sample = list(invalid.unique()[:5])
            errors.append(ValidationError(
                table=table_name,
                column=fk,
                message=(
                    f"foreign key '{fk}' has {len(invalid)} value(s) not in "
                    f"'{parent_table}.{parent_pk}' (e.g. {sample})"
                ),
            ))

    # 4. Enum columns: every value is in the allowed set.
    for (table_name, column), allowed in ENUMS.items():
        if not _has_column(table_name, column):
            continue
        df = tables[table_name]
        invalid = set(df[column].dropna().unique()) - allowed
        if invalid:
            errors.append(ValidationError(
                table=table_name,
                column=column,
                message=(
                    f"'{column}' has invalid values {sorted(invalid)}, "
                    f"expected one of {sorted(allowed)}"
                ),
            ))

    return errors


def format_errors(errors: list[ValidationError]) -> str:
    """Human-readable error report, one violation per line."""
    if not errors:
        return "No validation errors."
    lines = [f"{len(errors)} validation error(s):"]
    for err in errors:
        location = f"{err.table}.{err.column}" if err.column else err.table
        lines.append(f"  [{location}] {err.message}")
    return "\n".join(lines)
