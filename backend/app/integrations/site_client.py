"""Client for the Site Simulator API."""
from dotenv import load_dotenv
import os
from pathlib import Path
import httpx2 as httpx

PROJECT_ROOT = Path(__file__).resolve().parents[3]

class SiteClient:
    def __init__(self):
        load_dotenv(PROJECT_ROOT / '.env', override=True)
        base_url = os.getenv('CLIENT_BASE_URL')
        if not base_url:
            raise ValueError('CLIENT_BASE_URL is not set in the environment variables')
        self.base_url = base_url.strip('/')

    def get_shipments(self) -> list[dict]:
        response = httpx.Client().get(f'{self.base_url}/api/v1/shipments/')
        
        return response.json()['shipments']