from fastapi import APIRouter

TEST_SHIPMENTS = [
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
        'updated_at': '2026-08-26T05:14:22Z'
    }
]

router = APIRouter(prefix='/api/v1/shipments', tags=['Shipments'])


@router.get('')
async def get_shipments():
    """Return shipment rows for ReadinessIQ automated ingestion."""
    return {'status': 'ok', 'shipments': TEST_SHIPMENTS}
