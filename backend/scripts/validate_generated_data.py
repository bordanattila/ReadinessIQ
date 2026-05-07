from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'


REQUIRED_FILES = {
    'sites': DATA_DIR / 'sites.csv',
    'part_master': DATA_DIR / 'part_master.csv',
    'inventory_positions': DATA_DIR / 'inventory_positions.csv',
    'shipments': DATA_DIR / 'shipments.csv',
    'supplier_orders': DATA_DIR / 'supplier_orders.csv',
    'maintenance_events': DATA_DIR / 'maintenance_events.csv',
}


REQUIRED_COLUMNS = {
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
    },
    'supplier_orders': {
        'order_id',
        'order_supplier_id',
        'order_part_id',
        'order_quantity',
        'order_status',
        'order_created_at',
        'order_updated_at',
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

RED     = '\033[31m'
RESET   = '\033[0m'


def assert_files_exist() -> None:
    missing_files = [
        str(path)
        for path in REQUIRED_FILES.values()
        if not path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(f'{RED}Missing CSV files: {missing_files}{RESET}')


def load_dataframes() -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_csv(path)
        for name, path in REQUIRED_FILES.items()
    }


def validate_required_columns(dataframes: dict[str, pd.DataFrame]) -> None:
    for name, required_columns in REQUIRED_COLUMNS.items():
        actual_columns = set(dataframes[name].columns)
        missing_columns = required_columns - actual_columns

        if missing_columns:
            raise ValueError(
                f'{RED}{name}.csv is missing columns: {sorted(missing_columns)}{RESET}'
            )


def validate_foreign_keys(dataframes: dict[str, pd.DataFrame]) -> None:
    sites = dataframes['sites'].copy()
    parts = dataframes['part_master'].copy()
    inventory = dataframes['inventory_positions'].copy()
    shipments = dataframes['shipments'].copy()
    maintenance = dataframes['maintenance_events'].copy()

    valid_site_ids = set(sites['site_id'])
    valid_part_ids = set(parts['part_id'])

    checks = [
        ('inventory_positions.site_id', inventory['site_id'], valid_site_ids),
        ('inventory_positions.part_id', inventory['part_id'], valid_part_ids),
        ('shipments.site_id', shipments['site_id'], valid_site_ids),
        ('shipments.part_id', shipments['part_id'], valid_part_ids),
        ('maintenance_events.site_id', maintenance['site_id'], valid_site_ids),
        ('maintenance_events.part_id', maintenance['part_id'], valid_part_ids),
    ]

    for label, values, valid_values in checks:
        invalid_values = set(values) - valid_values

        if invalid_values:
            sample = list(invalid_values)[:10]
            raise ValueError(
                f'{RED}{label} has invalid references. Sample: {sample}{RESET}'
            )


def validate_inventory_logic(dataframes: dict[str, pd.DataFrame]) -> None:
    inventory = dataframes['inventory_positions'].copy()

    expected_available = (
        inventory['quantity_on_hand'] - inventory['quantity_allocated']
    )

    invalid_rows = inventory[
        inventory['quantity_available'] != expected_available
    ]

    if not invalid_rows.empty:
        raise ValueError(
            f'{RED}Inventory quantity logic failed for {len(invalid_rows)} rows.{RESET}'
        )


def validate_shipment_logic(dataframes: dict[str, pd.DataFrame]) -> None:
    shipments = dataframes['shipments'].copy()

    shipments['expected_delivery_date'] = pd.to_datetime(
        shipments['expected_delivery_date']
    )
    shipments['actual_delivery_date'] = pd.to_datetime(
        shipments['actual_delivery_date']
    )

    expected_delayed_flag = (
        shipments['actual_delivery_date'] > shipments['expected_delivery_date']
    )

    invalid_delay_flags = shipments[
        shipments['delayed_flag'] != expected_delayed_flag
    ]

    if not invalid_delay_flags.empty:
        raise ValueError(
            f'{RED}Shipment delay flag logic failed for {len(invalid_delay_flags)} rows.{RESET}'
        )


def validate_generated_data() -> None:
    assert_files_exist()
    dataframes = load_dataframes()

    validate_required_columns(dataframes)
    validate_foreign_keys(dataframes)
    validate_inventory_logic(dataframes)
    validate_shipment_logic(dataframes)

    print('Generated data validation passed.')
    print()
    for name, df in dataframes.items():
        print(f'{name}: {len(df):,} rows')


if __name__ == '__main__':
    validate_generated_data()