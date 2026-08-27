"""Tests for the /api/v1/shipments endpoint."""

import pytest
from fastapi.testclient import TestClient

SHIPMENTS_URL = '/api/v1/shipments'

EXPECTED_RESPONSE = {
    'status': 'ok',
    'shipments': [
        {
            'shipment_id': 'SHIP-83921',
            'site_id': 'SITE-001',
            'part_id': 'PART-00491',
            'ship_date': '2026-08-25',
            'expected_delivery_date': '2026-08-27',
            'actual_delivery_date': None,
            'quantity_shipped': 15,
            'shipment_status': 'shipped',
            'delayed_flag': False,
            'delay_days': 0,
            'supplier_id': 'SUP-001',
            'supplier_name': 'Acme Logistics',
            'updated_at': '2026-08-26T05:14:22Z',
        }
    ],
}


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def test_get_shipments_returns_status_ok(client):
    response = client.get(SHIPMENTS_URL)

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/json')
    assert response.json()['status'] == 'ok'


def test_get_shipments_returns_readinessiq_ingestion_shape(client):
    response = client.get(SHIPMENTS_URL)

    body = response.json()
    assert body == EXPECTED_RESPONSE
    assert isinstance(body['shipments'], list)
    assert len(body['shipments']) == 1


def test_post_shipments_is_not_allowed(client):
    response = client.post(SHIPMENTS_URL)

    assert response.status_code == 405
