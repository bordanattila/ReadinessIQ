"""Unit tests for shipment integration schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.integration.shipments import (
    ShipmentRecordIngestion,
    ShipmentsIngestionResponse,
)


def _valid_payload(**overrides) -> dict:
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


@pytest.mark.parametrize(
    ('overrides', 'label'),
    [
        ({}, 'in_transit'),
        (
            {
                'actual_delivery_date': '2026-08-27',
                'shipment_status': 'delivered',
            },
            'on_time',
        ),
        (
            {
                'actual_delivery_date': '2026-08-26',
                'shipment_status': 'delivered',
            },
            'early',
        ),
        (
            {
                'actual_delivery_date': '2026-08-30',
                'shipment_status': 'delivered',
                'delayed_flag': True,
                'delay_days': 3,
            },
            'late',
        ),
    ],
)
def test_accepts_valid_shipment_shapes(overrides, label):
    record = ShipmentRecordIngestion.model_validate(_valid_payload(**overrides))

    assert record.shipment_id == 'SHIP-83921'
    assert label in {'in_transit', 'on_time', 'early', 'late'}


@pytest.mark.parametrize(
    ('overrides', 'message'),
    [
        (
            {'expected_delivery_date': '2026-08-24'},
            'Expected delivery date must be on or after ship date',
        ),
        (
            {
                'actual_delivery_date': '2026-08-24',
                'delay_days': 0,
            },
            'Actual delivery date must be on or after ship date',
        ),
        (
            {'delayed_flag': True},
            'delayed_flag must be False when actual delivery date is missing',
        ),
        (
            {'delay_days': 1},
            'delay_days must be 0 when actual delivery date is missing',
        ),
        (
            {
                'actual_delivery_date': '2026-08-30',
                'delayed_flag': True,
                'delay_days': 1,
            },
            'delay_days must equal max\\(actual_delivery_date - expected_delivery_date, 0\\) in days',
        ),
        (
            {
                'actual_delivery_date': '2026-08-27',
                'delayed_flag': True,
                'delay_days': 0,
            },
            'delayed_flag must be False when delivery is on or before the expected date',
        ),
        (
            {
                'actual_delivery_date': '2026-08-26',
                'delayed_flag': True,
                'delay_days': 0,
            },
            'delayed_flag must be False when delivery is on or before the expected date',
        ),
        (
            {
                'actual_delivery_date': '2026-08-30',
                'delayed_flag': False,
                'delay_days': 3,
            },
            'delayed_flag must be True when delivery is after the expected date',
        ),
    ],
)
def test_rejects_invalid_delay_rules(overrides, message):
    with pytest.raises(ValidationError, match=message):
        ShipmentRecordIngestion.model_validate(_valid_payload(**overrides))


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('shipment_id', ''),
        ('quantity_shipped', 0),
        ('delay_days', -1),
    ],
)
def test_rejects_invalid_field_constraints(field, value):
    with pytest.raises(ValidationError):
        ShipmentRecordIngestion.model_validate(_valid_payload(**{field: value}))


def test_shipments_ingestion_response_wraps_records():
    response = ShipmentsIngestionResponse.model_validate(
        {
            'status': 'ok',
            'shipments': [_valid_payload()],
        }
    )

    assert response.status == 'ok'
    assert len(response.shipments) == 1
    assert response.shipments[0].shipment_id == 'SHIP-83921'
