import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pandas as pd
from sqlalchemy import create_engine
from utils.connect_to_db import get_database_url


CSV_TABLE_MAP = {
    "sites.csv": "sites",
    "part_master.csv": "part_master",
    "inventory_positions.csv": "inventory_positions",
    "shipments.csv": "shipments",
    "supplier_orders.csv": "supplier_orders",
    "maintenance_events.csv": "maintenance_events",
}

PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'

def load_csvs_to_postgres() -> None:
    """Load CSV files to PostgreSQL"""

    engine = create_engine(get_database_url())

    for csv_file, table_name in CSV_TABLE_MAP.items():
        csv_path = DATA_DIR / csv_file

        if not csv_path.exists():
            raise FileNotFoundError(f'CSV file {csv_path} not found')

        df = pd.read_csv(csv_path)
        df.to_sql(
            table_name, 
            engine, 
            if_exists='replace', 
            index=False,
            )

    print('CSV files loaded to PostgreSQL successfully')

if __name__ == '__main__':
    load_csvs_to_postgres()
    print('CSV load completed successfully.')