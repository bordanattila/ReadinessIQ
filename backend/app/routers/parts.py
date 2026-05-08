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
