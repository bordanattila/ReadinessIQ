"""
A script that generates realistic synthetic CSVs for:
1. sites
2. part_master
3. inventory_positions
4. shipments
5. supplier_orders
6. maintenance_events
"""

import pandas as pd
import random
import datetime
from data_generator_support_files.data_generator_sites_lists import sites as sites_list
from data_generator_support_files.generate_parts_master_1000 import parts_master as parts_master_list
from data_generator_support_files.supplier_list import supplier_names as supplier_list
from datetime import date, timedelta
from pathlib import Path

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_random_date(start_year: int = 2023, start_month: int = 1, start_day: int = 1) -> date:
    return date(random.randint(start_year, 2026), random.randint(start_month, 12), random.randint(start_day, 28))

# Generate sites data
def generate_sites_data(num_sites: int = 100) -> pd.DataFrame:
    """Generate synthetic site data with random names and locations"""
    sites = []
    for site_item in sites_list:
        site = {
            'site_id': site_item['site_id'],
            'site_name': site_item['site_name'],
            'site_region': site_item['region'],
            'site_type': site_item['site_type'],
            'site_mission_priority': site_item['mission_priority'],
            'site_active_flag': site_item['active_flag'],
        }
        sites.append(site)
    return pd.DataFrame(sites)

# Generate part_master data with sequential part numbers
def generate_part_master_data(num_parts=1000):
    """Generate synthetic part master data with sequential part numbers."""
    parts = []
    # Sequential IDs avoid birthday-paradox collisions you'd get from
    # random.randint(1000, 9999) when generating ~1000 parts. The :04d format
    # zero-pads so PART-0001 sorts lexicographically with PART-1000.
    for index, part_item in enumerate(parts_master_list, start=1):
        part = {
            'part_id': f'PART-{index:04d}',
            'nsn': f'{random.randint(0, 1000)}-{random.randint(0, 1000)}-{random.randint(0, 1000)}-{random.randint(0, 1000)}',
            'part_name': part_item['part_name'],
            'part_family': part_item['part_family'],
            'criticality': part_item['criticality'],
        }
        parts.append(part)
    return pd.DataFrame(parts)

# Generate inventory_positions data with random inventory levels
def generate_inventory_positions_data(sites_df: pd.DataFrame, parts_df: pd.DataFrame, num_positions: int = 5000) -> pd.DataFrame:
    """Generate synthetic inventory position data with random inventory levels"""
    positions = []

    site_records = sites_df.to_dict(orient='records')
    part_records = parts_df.to_dict(orient='records')

    for i in range(num_positions):
        site = random.choice(site_records)
        part = random.choice(part_records)

        quantity_on_hand = random.randint(0, 500)
        quantity_allocated = random.randint(0, quantity_on_hand)
        quantity_available = quantity_on_hand - quantity_allocated

        reorder_point = random.randint(20, 100)
        safety_stock = random.randint(10, reorder_point)

        stockout_flag = quantity_available == 0
        below_reorder_point = quantity_available < reorder_point
        below_safety_stock = quantity_available < safety_stock

        average_daily_demand = random.randint(1, 25)
        days_of_supply = round(quantity_available / average_daily_demand, 1)

        position = {
            "inventory_id": i + 1,
            "site_id": site["site_id"],
            "part_id": part["part_id"],
            "quantity_on_hand": quantity_on_hand,
            "quantity_allocated": quantity_allocated,
            "quantity_available": quantity_available,
            "reorder_point": reorder_point,
            "safety_stock": safety_stock,
            "stockout_flag": stockout_flag,
            "below_reorder_point": below_reorder_point,
            "below_safety_stock": below_safety_stock,
            "days_of_supply": days_of_supply,
            "snapshot_date": get_random_date(),
        }
        positions.append(position)
    return pd.DataFrame(positions)

# Generate shipments data with random shipment dates and statuses
def generate_shipments_data(sites_df: pd.DataFrame, parts_df: pd.DataFrame, num_shipments: int = 10000) -> pd.DataFrame:
    """Generate synthetic shipment data with random shipment dates and statuses"""
    shipments = []

    site_records = sites_df.to_dict(orient='records')
    part_records = parts_df.to_dict(orient='records')

    for i in range(num_shipments):
        site = random.choice(site_records)
        part = random.choice(part_records)
        supplier_name = random.choice(supplier_list)
        supplier_id = _generate_supplier_id(supplier_name)

        ship_date = get_random_date(2025)
        expected_delivery_date = ship_date + timedelta(days=random.randint(3, 10))

        # Model on-time vs. delayed as two separate regimes so the delay rate
        # reflects real-world supply chains (~12% late) instead of falling out
        # of overlapping uniform ranges.
        if random.random() < 0.12:
            # Right-skewed delay: most delays small, occasional long tail.
            delay = max(1, int(random.triangular(1, 21, 4)))
            actual_delivery_date = expected_delivery_date + timedelta(days=delay)
        else:
            # On-time arrivals: same day or slightly early.
            actual_delivery_date = expected_delivery_date + timedelta(days=random.randint(-2, 0))

        delayed_flag = actual_delivery_date > expected_delivery_date
        delay_days = max((actual_delivery_date - expected_delivery_date).days, 0)

        shipment = {
            'shipment_id': i + 1,
            'site_id': site['site_id'],
            'part_id': part['part_id'],
            'ship_date': ship_date,
            'expected_delivery_date': expected_delivery_date,
            'actual_delivery_date': actual_delivery_date,
            'quantity_shipped': random.randint(1, 1000),
            'shipment_status': random.choice(['pending', 'shipped', 'delivered']),
            'delayed_flag': delayed_flag,
            'delay_days': delay_days,
            'supplier_id': supplier_id,
            'supplier_name': supplier_name,
        }
        shipments.append(shipment)
    return pd.DataFrame(shipments)

# Generate supplier_orders data with random order dates and statuses
def _generate_supplier_id(supplier_name: str) -> str:
    supplier_id = ""
    for i in range(len(supplier_name)):
        if supplier_name[i].isupper():
            supplier_id += supplier_name[i]
    return supplier_id

def generate_supplier_orders_data(
    sites_df: pd.DataFrame,
    parts_df: pd.DataFrame,
    num_orders: int = 10000,
) -> pd.DataFrame:
    """Generate synthetic supplier order data with random order dates and statuses.

    ``order_part_id`` is always a ``part_master.part_id`` string. ``site_id``
    is the customer site this order supports (for supplier coverage metrics).
    """
    orders = []

    part_records = parts_df.to_dict(orient='records')
    site_records = sites_df.to_dict(orient='records')

    for i in range(num_orders):
        supplier_name = random.choice(supplier_list)
        order_created_at = get_random_date()

        part = random.choice(part_records)
        site = random.choice(site_records)

        order = {
            'order_id': i + 1,
            'order_supplier_name': supplier_name,
            'order_supplier_id': _generate_supplier_id(supplier_name),
            'order_part_id': part['part_id'],
            'order_quantity': random.randint(0, 1000),
            'order_status': random.choice(['pending', 'shipped', 'delivered']),
            'order_created_at': order_created_at,
            'order_updated_at': order_created_at + timedelta(days=random.randint(1, 30)),
            'site_id': site['site_id'],
        }
        orders.append(order)
    return pd.DataFrame(orders)

# Generate maintenance_events data with random event dates and statuses
def generate_maintenance_events_data(sites_df: pd.DataFrame, parts_df: pd.DataFrame, num_events: int = 10000) -> pd.DataFrame:
    """Generate synthetic maintenance event data with random event dates and statuses"""
    events = []

    site_records = sites_df.to_dict(orient='records')
    part_records = parts_df.to_dict(orient='records')

    for i in range(num_events):
        site = random.choice(site_records)
        part = random.choice(part_records)

        event_date = get_random_date()
        status = random.choice(["open", "in_progress", "awaiting_parts", "completed", "deferred"])

        if status == "completed":
            days_non_mission_capable = random.randint(0, 10)
            backlog_days = 0
        else:
            days_non_mission_capable = random.randint(1, 30)
            backlog_days = random.randint(1, 45)

        defect_flag = random.random() < 0.12

        event = {
            "maintenance_event_id": i + 1,
            "site_id": site["site_id"],
            "part_id": part["part_id"],
            "event_date": event_date,
            "equipment_id": f"EQ-{random.randint(1000, 9999)}",
            "status": status,
            "days_non_mission_capable": days_non_mission_capable,
            "backlog_days": backlog_days,
            "defect_flag": defect_flag,
        }
        events.append(event)
    return pd.DataFrame(events)

# Generate all data
def generate_all_data():
    """Generate all synthetic data"""
    sites = generate_sites_data()
    parts = generate_part_master_data()
    inventory = generate_inventory_positions_data(
        sites_df=sites,
        parts_df=parts
    )
    shipments = generate_shipments_data(
        sites_df=sites,
        parts_df=parts
    )
    orders = generate_supplier_orders_data(sites_df=sites, parts_df=parts)
    events = generate_maintenance_events_data(
        sites_df=sites,
        parts_df=parts
    )
    return sites, parts, inventory, shipments, orders, events

# Generate all data and save to CSV
def generate_and_save_all_data():
    """Generate all synthetic data and save to CSV"""
    sites, parts, inventory, shipments, orders, events = generate_all_data()
    sites.to_csv(OUTPUT_DIR / "sites.csv", index=False)
    parts.to_csv(OUTPUT_DIR / "part_master.csv", index=False)
    inventory.to_csv(OUTPUT_DIR / "inventory_positions.csv", index=False)
    shipments.to_csv(OUTPUT_DIR / "shipments.csv", index=False)
    orders.to_csv(OUTPUT_DIR / "supplier_orders.csv", index=False)
    events.to_csv(OUTPUT_DIR / "maintenance_events.csv", index=False)


if __name__ == "__main__":
    generate_and_save_all_data()
    print("Synthetic data generated successfully.")