"""Part-level readiness risk — answers "Which parts are driving readiness risk?"

Aggregates inventory posture, open maintenance, and delayed shipments per
`part_id`, joins `part_master` for descriptive fields, then scores and ranks.

How it's computed
Field	                        Meaning
sites_impacted	                Distinct sites where that part has at least one of: stockout, below reorder, or below safety stock
stockout_count	                Rows in inventory_positions with stockout_flag for that part_id
below_reorder_count	            Rows with below_reorder_point
total_quantity_available	    SUM(quantity_available) across all positions for that part
open_maintenance_events	        Rows in maintenance_events with status = 'open' for that part
delayed_shipments	            Rows in shipments with delayed_flag for that part
readiness_risk_score	        Weighted raw score (inventory + maintenance + delayed shipments on that part), normalized to 0-100
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine


router = APIRouter(prefix='/api/parts', tags=['Parts'])

# Part-level readiness impact uses inventory constraints, open maintenance demand,
# and inbound shipment disruption. Mission priority is excluded because it applies
# to sites, not SKUs. Criticality is applied as a multiplier so mission-critical
# parts rank above lower-criticality parts with similar operational signals.
_PART_RISK_WEIGHTS = {
    'stockout': 0.35,
    'below_reorder': 0.20,
    'open_maintenance': 0.25,
    'delayed_shipments': 0.20,
}

# Tier multiplier so Mission Critical / High parts surface above noisy counts alone.
_CRITICALITY_MULT = {
    'Mission Critical': 1.15,
    'High': 1.10,
    'Medium': 1.0,
    'Low': 0.90,
}

_PART_READINESS_SQL = """
WITH inv AS (
    SELECT
        part_id,
        COUNT(DISTINCT CASE
            WHEN stockout_flag OR below_reorder_point OR below_safety_stock
            THEN site_id
        END) AS sites_impacted,
        SUM(CASE WHEN stockout_flag THEN 1 ELSE 0 END) AS stockout_count,
        SUM(CASE WHEN below_reorder_point THEN 1 ELSE 0 END) AS below_reorder_count,
        SUM(COALESCE(quantity_available, 0)) AS total_quantity_available
    FROM inventory_positions
    GROUP BY part_id
),
maint AS (
    SELECT
        part_id,
        SUM(CASE WHEN status = :open_status THEN 1 ELSE 0 END) AS open_maintenance_events
    FROM maintenance_events
    GROUP BY part_id
),
ship AS (
    SELECT
        part_id,
        SUM(CASE WHEN delayed_flag THEN 1 ELSE 0 END) AS delayed_shipments
    FROM shipments
    GROUP BY part_id
)
SELECT
    p.part_id,
    p.part_name,
    p.part_family,
    p.criticality,
    COALESCE(inv.sites_impacted, 0) AS sites_impacted,
    COALESCE(inv.stockout_count, 0) AS stockout_count,
    COALESCE(inv.below_reorder_count, 0) AS below_reorder_count,
    COALESCE(inv.total_quantity_available, 0) AS total_quantity_available,
    COALESCE(maint.open_maintenance_events, 0) AS open_maintenance_events,
    COALESCE(ship.delayed_shipments, 0) AS delayed_shipments
FROM part_master p
LEFT JOIN inv   ON inv.part_id   = p.part_id
LEFT JOIN maint ON maint.part_id = p.part_id
LEFT JOIN ship  ON ship.part_id  = p.part_id
"""

_NUMERIC_FIELDS = (
    'sites_impacted',
    'stockout_count',
    'below_reorder_count',
    'total_quantity_available',
    'open_maintenance_events',
    'delayed_shipments',
)


def _coerce_numeric_fields(row: dict) -> None:
    for field in _NUMERIC_FIELDS:
        row[field] = float(row[field])


def _raw_part_risk_score(row: dict) -> float:
    crit = row.get('criticality') or 'Medium'
    mult = _CRITICALITY_MULT.get(crit, 1.0)
    base = (
        row['stockout_count']           * _PART_RISK_WEIGHTS['stockout']
        + row['below_reorder_count']    * _PART_RISK_WEIGHTS['below_reorder']
        + row['open_maintenance_events'] * _PART_RISK_WEIGHTS['open_maintenance']
        + row['delayed_shipments']      * _PART_RISK_WEIGHTS['delayed_shipments']
    )
    return base * mult


# Primary supplier for a part: most activity across shipments + supplier_orders.
_PART_PRIMARY_SUPPLIER_SQL = """
WITH activity AS (
    SELECT supplier_id, supplier_name, activity_weight, source
    FROM (
        SELECT
            supplier_id,
            MAX(supplier_name) AS supplier_name,
            COUNT(*) AS activity_weight,
            'shipment' AS source
        FROM shipments
        WHERE part_id = :part_id
          AND supplier_id IS NOT NULL
          AND supplier_id != ''
        GROUP BY supplier_id
        UNION ALL
        SELECT
            order_supplier_id AS supplier_id,
            MAX(order_supplier_name) AS supplier_name,
            COUNT(*) AS activity_weight,
            'order' AS source
        FROM supplier_orders
        WHERE order_part_id = :part_id
          AND order_supplier_id IS NOT NULL
          AND order_supplier_id != ''
        GROUP BY order_supplier_id
    ) src
)
SELECT
    supplier_id,
    MAX(supplier_name) AS supplier_name
FROM activity
GROUP BY supplier_id
ORDER BY
    SUM(CASE WHEN source = 'shipment' THEN activity_weight ELSE 0 END) DESC,
    SUM(activity_weight) DESC
LIMIT 1
"""


def _part_supplier_payload(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {
        'supplier_id': row['supplier_id'],
        'supplier_name': row['supplier_name'],
    }


@router.get('/readiness-impact')
def get_parts_readiness_impact(engine: Engine = Depends(get_engine)):
    """Rank parts by contribution to readiness risk (highest first).

    Each row summarizes enterprise-wide exposure for one SKU: how many sites
    show distress for that part, inventory indicators, open maintenance tied
    to the part, delayed inbound shipments, and a 0–100 ``readiness_risk_score``
    normalized against the worst part in the current snapshot.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(_PART_READINESS_SQL),
                {'open_status': 'open'},
            )
            rows = [dict(r) for r in result.mappings().all()]

        if not rows:
            return {'status': 'ok', 'parts': []}

        for row in rows:
            _coerce_numeric_fields(row)
            row['_raw_score'] = _raw_part_risk_score(row)

        max_raw = max(r['_raw_score'] for r in rows) or 1.0

        out = []
        for row in rows:
            readiness_risk_score = round(row.pop('_raw_score') / max_raw * 100, 1)
            # Strip helper column used only for scoring; keep API stable for callers.
            row.pop('delayed_shipments', None)
            row['readiness_risk_score'] = readiness_risk_score
            # Round integers that should display as whole counts.
            row['sites_impacted'] = int(row['sites_impacted'])
            row['stockout_count'] = int(row['stockout_count'])
            row['below_reorder_count'] = int(row['below_reorder_count'])
            row['total_quantity_available'] = int(row['total_quantity_available'])
            row['open_maintenance_events'] = int(row['open_maintenance_events'])
            out.append(row)

        out.sort(key=lambda r: r['readiness_risk_score'], reverse=True)

        return {'status': 'ok', 'parts': out}

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
        }

@router.get('/{part_id}/summary')
def get_part_summary(part_id: str, engine: Engine = Depends(get_engine)):
    """Return a detailed readiness summary for a single part.

        Args:
        part_id: The part identifier, e.g. ``"PART-001"``.

        Returns:
            On success, a JSON object shaped like::
            {
                "status": "ok",
                "part": {
                    "part_id": "PART-001",
                    "part_name": "Hydraulic Seal Kit",
                    "part_family": "Hydraulics",
                    "criticality": "High",
                },
                "supplier": {
                    "supplier_id": "SUP-001",
                    "supplier_name": "Supplier Inc.",
                },
                "inventory": {
                    "stockout_count": 3,
                    "below_reorder_count": 18,
                    "below_safety_stock_count": 9,
                },
                "shipments": {
                    "total_shipments": 104,
                    "delayed_shipments": 27,
                    "delayed_shipment_rate": 0.2596,
                    "average_delay_days": 3.7,
                },
                "sites_impacted": [
                    {
                        "site_id": "SITE-001",
                        "site_name": "Fort Liberty Sustainment Hub",
                        "site_region": "Southeast",
                        "site_type": "Depot",
                        "mission_priority": 5,
                    }
                ],
            }
    """

    try:
        with engine.connect() as conn:
            params = {'part_id': part_id}

            # Part metadata. `mappings().first()` gives a dict-like single row
            # or None if no part matches.
            part = conn.execute(
                text("""
                    SELECT
                        part_id,
                        part_name,
                        part_family,
                        criticality
                    FROM part_master
                    WHERE part_id = :part_id
                """),
                params,
            ).mappings().first()

            if part is None:
                return {
                    'status': 'error',
                    'message': f'Part {part_id!r} not found',
                }

            # All four aggregate queries below use SUM(CASE WHEN ...) so the
            # result is always a single row (even when the part has zero
            # inventory / shipments / maintenance events).
            inventory = conn.execute(
                text("""
                    SELECT
                        COALESCE(SUM(CASE WHEN stockout_flag THEN 1 ELSE 0 END), 0)
                            AS stockout_count,
                        COALESCE(SUM(CASE WHEN below_reorder_point THEN 1 ELSE 0 END), 0)
                            AS below_reorder_count,
                        COALESCE(SUM(CASE WHEN below_safety_stock THEN 1 ELSE 0 END), 0)
                            AS below_safety_stock_count
                    FROM inventory_positions
                    WHERE part_id = :part_id
                """),
                params,
            ).mappings().first()

            shipments = conn.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_shipments,
                        COALESCE(SUM(CASE WHEN delayed_flag THEN 1 ELSE 0 END), 0)
                            AS delayed_shipments,
                        AVG(CASE WHEN delayed_flag THEN delay_days END)
                            AS average_delay_days
                    FROM shipments
                    WHERE part_id = :part_id
                """),
                params,
            ).mappings().first()

            # Sites are linked to parts through inventory_positions, not a part_id
            # column on sites. Match readiness-impact: sites with stockout,
            # below reorder, or below safety stock for this part.
            sites_impacted = conn.execute(
                text("""
                    SELECT DISTINCT
                        s.site_id,
                        s.site_name,
                        s.site_region,
                        s.site_type,
                        s.site_mission_priority AS mission_priority
                    FROM inventory_positions i
                    JOIN sites s ON s.site_id = i.site_id
                    WHERE i.part_id = :part_id
                      AND (
                          i.stockout_flag
                          OR i.below_reorder_point
                          OR i.below_safety_stock
                      )
                    ORDER BY mission_priority DESC, s.site_name
                """),
                params,
            ).mappings().all()

            supplier = conn.execute(
                text(_PART_PRIMARY_SUPPLIER_SQL),
                params,
            ).mappings().first()

        total_shipments = int(shipments['total_shipments'])
        delayed_shipments = int(shipments['delayed_shipments'])
        delayed_rate = (
            delayed_shipments / total_shipments if total_shipments > 0 else 0
        )

        return {
            'status': 'ok',
            'part': dict(part),
            'supplier': _part_supplier_payload(dict(supplier) if supplier else None),
            'sites_impacted': [dict(s) for s in sites_impacted],
            'inventory': {
                'stockout_count': int(inventory['stockout_count']),
                'below_reorder_count': int(inventory['below_reorder_count']),
                'below_safety_stock_count': int(inventory['below_safety_stock_count']),
            },
            'shipments': {
                'total_shipments': total_shipments,
                'delayed_shipments': delayed_shipments,
                'delayed_shipment_rate': round(delayed_rate, 4),
                'average_delay_days': round(float(shipments['average_delay_days'] or 0), 2),
            },
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
        }
