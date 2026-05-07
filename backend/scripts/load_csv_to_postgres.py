from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'

CSV_TABLE_MAP = {
    "sites.csv": "sites",
    "part_master.csv": "part_master",
    "inventory_positions.csv": "inventory_positions",
    "shipments.csv": "shipments",
    "supplier_orders.csv": "supplier_orders",
    "maintenance_events.csv": "maintenance_events",
}

def get_database_url():
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError('DATABASE_URL is not set in the environment variables')
    return database_url

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