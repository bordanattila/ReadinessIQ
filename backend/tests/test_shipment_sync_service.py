"""Unit tests for `app.integrations.shipment_sync_service`."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.integrations.shipment_sync_service import ShipmentSyncService


def _valid_raw_shipment(**overrides) -> dict:
    payload = {
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
    payload.update(overrides)
    return payload


def test_sync_shipments_returns_validated_records():
    service = ShipmentSyncService()
    service.site_client = MagicMock()
    service.site_client.get_shipments.return_value = [_valid_raw_shipment()]

    result = service.sync_shipments()

    assert result.status == 'ok'
    assert len(result.shipments) == 1
    assert result.shipments[0].shipment_id == 'SHIP-83921'
    assert result.shipments[0].updated_at is not None


def test_sync_shipments_skips_invalid_rows_and_keeps_valid_ones():
    service = ShipmentSyncService()
    service.site_client = MagicMock()
    service.site_client.get_shipments.return_value = [
        _valid_raw_shipment(shipment_id='SHIP-VALID'),
        _valid_raw_shipment(
            shipment_id='SHIP-BAD',
            actual_delivery_date='2026-08-30',
            delayed_flag=False,
            delay_days=3,
        ),
    ]

    result = service.sync_shipments()

    assert result.status == 'ok'
    assert [shipment.shipment_id for shipment in result.shipments] == ['SHIP-VALID']


def test_sync_shipments_raises_when_client_fails():
    service = ShipmentSyncService()
    service.site_client = MagicMock()
    service.site_client.get_shipments.side_effect = RuntimeError('simulator unavailable')

    with pytest.raises(ValueError, match='Error syncing shipments: simulator unavailable'):
        service.sync_shipments()
