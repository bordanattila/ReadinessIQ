"""Supplier performance API.

Response rows resemble::

    {
        "supplier_name": "Apex Defense Components",
        "total_orders": 142,
        "open_orders": 31,
        "delayed_shipments": 18,
        "average_delay_days": 4.7,
        "on_time_delivery_rate": 0.873,
        "parts_supported": 46,
        "sites_supported": 12,
        "performance_risk_score": 78.4
    }
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine

router = APIRouter(prefix='/api/suppliers', tags=['Suppliers'])

_SUPPLIER_RISK_WEIGHTS = {
    'open_orders': 0.30,
    'delayed_shipments': 0.20,
    'average_delay_days': 0.20,
    'on_time_delivery_rate': 0.20,
    'sites_supported': 0.10,
    'parts_supported': 0.10,
}

# Derived from supplier_orders + shipments (no separate ``suppliers`` table).
# ``on_time_delivery_rate`` is (total - delayed) / total shipments; 1.0 when
# there are no shipments. DMNC is averaged over maintenance_events that share
# site_id + part_id with a shipment row for that supplier.
_SUPPLIERS_SQL = """
WITH supplier_dim AS (
    SELECT supplier_id, MAX(supplier_name) AS supplier_name
    FROM (
        SELECT order_supplier_id AS supplier_id, order_supplier_name AS supplier_name
        FROM supplier_orders
        UNION ALL
        SELECT supplier_id, supplier_name FROM shipments
    ) u
    GROUP BY supplier_id
),
orders_agg AS (
    SELECT
        order_supplier_id AS supplier_id,
        COUNT(*) AS total_orders,
        SUM(CASE WHEN order_status = 'pending' THEN 1 ELSE 0 END) AS open_orders
    FROM supplier_orders
    GROUP BY order_supplier_id
),
shipments_agg AS (
    SELECT
        supplier_id,
        COUNT(*) AS total_shipments,
        SUM(CASE WHEN delayed_flag THEN 1 ELSE 0 END) AS delayed_shipments,
        AVG(delay_days) AS average_delay_days
    FROM shipments
    GROUP BY supplier_id
),
coverage AS (
    SELECT
        supplier_id,
        COUNT(DISTINCT site_id) AS sites_supported,
        COUNT(DISTINCT part_id) AS parts_supported
    FROM (
        SELECT order_supplier_id AS supplier_id, site_id, order_part_id AS part_id
        FROM supplier_orders
        UNION
        SELECT supplier_id, site_id, part_id FROM shipments
    ) x
    GROUP BY supplier_id
),
dmnc AS (
    SELECT
        sh.supplier_id,
        AVG(me.days_non_mission_capable) AS average_days_non_mission_capable
    FROM shipments sh
    INNER JOIN maintenance_events me
        ON me.site_id = sh.site_id AND me.part_id = sh.part_id
    GROUP BY sh.supplier_id
)
SELECT
    d.supplier_id,
    d.supplier_name,
    COALESCE(o.total_orders, 0) AS total_orders,
    COALESCE(o.open_orders, 0) AS open_orders,
    COALESCE(sh.total_shipments, 0) AS total_shipments,
    COALESCE(sh.delayed_shipments, 0) AS delayed_shipments,
    COALESCE(sh.average_delay_days, 0) AS average_delay_days,
    CASE
        WHEN COALESCE(sh.total_shipments, 0) = 0 THEN 1.0
        ELSE ROUND(
            CAST(
                CAST(sh.total_shipments - sh.delayed_shipments AS REAL)
                / CAST(NULLIF(sh.total_shipments, 0) AS REAL)
                AS NUMERIC
            ),
            3
        )
    END AS on_time_delivery_rate,
    COALESCE(c.sites_supported, 0) AS sites_supported,
    COALESCE(c.parts_supported, 0) AS parts_supported,
    ROUND(CAST(COALESCE(dm.average_days_non_mission_capable, 0) AS NUMERIC), 2)
        AS average_days_non_mission_capable
FROM supplier_dim d
LEFT JOIN orders_agg o ON d.supplier_id = o.supplier_id
LEFT JOIN shipments_agg sh ON d.supplier_id = sh.supplier_id
LEFT JOIN coverage c ON d.supplier_id = c.supplier_id
LEFT JOIN dmnc dm ON d.supplier_id = dm.supplier_id
"""

_COUNT_FIELDS = (
    'total_orders',
    'open_orders',
    'total_shipments',
    'delayed_shipments',
    'sites_supported',
    'parts_supported',
)

_FLOAT_FIELDS = (
    'average_delay_days',
    'on_time_delivery_rate',
    'average_days_non_mission_capable',
)


def _coerce_row_fields(row: dict) -> None:
    for field in _COUNT_FIELDS:
        v = row[field]
        row[field] = int(v) if v is not None else 0
    for field in _FLOAT_FIELDS:
        v = row[field]
        row[field] = float(v) if v is not None else 0.0


def _raw_supplier_risk_score(row: dict) -> float:
    # Higher on-time delivery => lower risk (invert into a "lateness" term).
    on_time_risk = 1.0 - row['on_time_delivery_rate']
    return (
        row['open_orders'] * _SUPPLIER_RISK_WEIGHTS['open_orders']
        + row['delayed_shipments'] * _SUPPLIER_RISK_WEIGHTS['delayed_shipments']
        + row['average_delay_days'] * _SUPPLIER_RISK_WEIGHTS['average_delay_days']
        + on_time_risk * _SUPPLIER_RISK_WEIGHTS['on_time_delivery_rate']
        + row['sites_supported'] * _SUPPLIER_RISK_WEIGHTS['sites_supported']
        + row['parts_supported'] * _SUPPLIER_RISK_WEIGHTS['parts_supported']
    )


@router.get('/performance')
def get_suppliers_performance(engine: Engine = Depends(get_engine)):
    """Return every supplier with performance metrics (highest risk score first)."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(_SUPPLIERS_SQL)).mappings().all()
            rows = [dict(r) for r in result]

        if not rows:
            return {'status': 'ok', 'suppliers': []}

        for row in rows:
            _coerce_row_fields(row)
            row['_raw_score'] = _raw_supplier_risk_score(row)

        max_raw = max(r['_raw_score'] for r in rows) or 1.0
        for row in rows:
            row['performance_risk_score'] = round(row.pop('_raw_score') / max_raw * 100, 1)
            row['average_days_non_mission_capable'] = round(
                row['average_days_non_mission_capable'], 2
            )

        for row in rows:
            row['risk_drivers'] = [
                f"{row['open_orders']} open_orders",
                f"{row['delayed_shipments']} delayed_shipments",
                f"{row['average_delay_days']:.2f} average_delay_days",
            ]

        rows.sort(key=lambda r: r['performance_risk_score'], reverse=True)

        return {'status': 'ok', 'suppliers': rows}
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
        }
