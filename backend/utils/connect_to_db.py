from dotenv import load_dotenv
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_database_url():
    load_dotenv(PROJECT_ROOT / '.env', override=True)
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError('DATABASE_URL is not set in the environment variables')
    return database_url