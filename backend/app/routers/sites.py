from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine


router = APIRouter(prefix='/api/sites', tags=['Sites'])


# Weights for the readiness risk score. Tuned so each site's raw score is then
# normalized to 0-100 across the whole result set for easy comparison.
_RISK_WEIGHTS = {
    'stockout': 0.30,
    'below_reorder': 0.20,
    'delayed_shipments': 0.20,
    'maintenance_backlog': 0.20,
    'mission_priority': 0.10,
}


_RISK_RANKING_SQL = """
WITH inv AS (
    SELECT
        site_id,
        SUM(CASE WHEN stockout_flag THEN 1 ELSE 0 END) AS stockout_count,
        SUM(CASE WHEN below_reorder_point THEN 1 ELSE 0 END) AS below_reorder_count
    FROM inventory_positions
    GROUP BY site_id
),
ship AS (
    SELECT
        site_id,
        SUM(CASE WHEN delayed_flag THEN 1 ELSE 0 END) AS delayed_count
    FROM shipments
    GROUP BY site_id
),
maint AS (
    SELECT
        site_id,
        SUM(CASE WHEN status = :open_status THEN 1 ELSE 0 END) AS open_count,
        AVG(CASE WHEN status = :open_status THEN backlog_days END) AS avg_backlog_days
    FROM maintenance_events
    GROUP BY site_id
)
SELECT
    s.site_id,
    s.site_name,
    s.site_region,
    s.site_type,
    s.site_mission_priority AS mission_priority,
    COALESCE(inv.stockout_count, 0) AS stockout_count,
    COALESCE(inv.below_reorder_count, 0) AS below_reorder_count,
    COALESCE(ship.delayed_count, 0) AS delayed_shipments,
    COALESCE(maint.open_count, 0) AS open_maintenance_events,
    COALESCE(maint.avg_backlog_days, 0) AS avg_backlog_days
FROM sites s
LEFT JOIN inv   ON inv.site_id   = s.site_id
LEFT JOIN ship  ON ship.site_id  = s.site_id
LEFT JOIN maint ON maint.site_id = s.site_id
"""


_NUMERIC_FIELDS = (
    'stockout_count',
    'below_reorder_count',
    'delayed_shipments',
    'open_maintenance_events',
    'avg_backlog_days',
    'mission_priority',
)


def _coerce_numeric_fields(row: dict) -> None:
    """Cast numeric columns to float in place.

    Postgres returns SUM()/AVG() over numeric columns as `decimal.Decimal`,
    which can't be multiplied by Python floats (the weights below). Casting
    once up front keeps the rest of the math readable.
    """
    for field in _NUMERIC_FIELDS:
        row[field] = float(row[field])


def _raw_risk_score(row: dict) -> float:
    return (
        row['stockout_count']           * _RISK_WEIGHTS['stockout']
        + row['below_reorder_count']    * _RISK_WEIGHTS['below_reorder']
        + row['delayed_shipments']      * _RISK_WEIGHTS['delayed_shipments']
        + row['avg_backlog_days']       * _RISK_WEIGHTS['maintenance_backlog']
        + row['mission_priority']       * _RISK_WEIGHTS['mission_priority']
    )


@router.get('/risk-ranking')
def get_sites_risk_ranking(engine: Engine = Depends(get_engine)):
    """Return every site ranked by readiness risk (highest risk first).

    The risk score is a weighted sum of stockouts, reorder breaches, delayed
    shipments, open-maintenance backlog, and mission priority — then
    normalized to a 0-100 scale across the result set.
    """
    try:
        with engine.connect() as conn:
            # Bind `:open_status` rather than interpolating to keep the query
            # injection-safe; `result.mappings()` gives dict-like rows we can
            # mutate when computing scores below.
            result = conn.execute(
                text(_RISK_RANKING_SQL),
                {'open_status': 'open'},
            )
            rows = [dict(r) for r in result.mappings().all()]

        # No sites in the DB -> return an empty list rather than 500-ing on
        # the `max(...)` call below.
        if not rows:
            return {'status': 'ok', 'sites': []}

        # First pass: cast Decimal -> float (Postgres aggregates) and compute
        # each site's raw weighted score.
        for row in rows:
            _coerce_numeric_fields(row)
            row['_raw_score'] = _raw_risk_score(row)

        # Normalize to 0-100 against the riskiest site. `or 1.0` guards
        # against a division-by-zero when every site has a raw score of 0
        # (e.g. a freshly seeded DB with no issues anywhere).
        max_raw = max(row['_raw_score'] for row in rows) or 1.0
        for row in rows:
            row['readiness_risk_score'] = round(row.pop('_raw_score') / max_raw * 100, 1)
            row['avg_backlog_days'] = round(row['avg_backlog_days'], 2)

        # Sort highest-risk-first so the response *is* the ranking.
        rows.sort(key=lambda r: r['readiness_risk_score'], reverse=True)

        return {'status': 'ok', 'sites': rows}

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
        }


@router.get('/{site_id}/summary')
def get_site_summary(site_id: str, engine: Engine = Depends(get_engine)):
    """Return a detailed readiness summary for a single site.

    Aggregates inventory, shipment, and maintenance metrics scoped to one
    site, plus the top constrained parts (those most starved of stock).

    Args:
        site_id: The site identifier, e.g. ``"SITE-001"``.

    Returns:
        On success, a JSON object shaped like::

            {
                "status": "ok",
                "site": {
                    "site_id": "SITE-001",
                    "site_name": "Fort Liberty Sustainment Hub",
                    "site_region": "Southeast",
                    "site_type": "Depot",
                    "mission_priority": 5,
                },
                "inventory": {
                    "total_inventory_positions": 52,
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
                "maintenance": {
                    "open_maintenance_events": 14,
                    "average_backlog_days": 21.4,
                    "total_days_non_mission_capable": 166,
                },
                "top_constrained_parts": [
                    {
                        "part_id": "PART-0042",
                        "part_name": "Hydraulic Seal Kit",
                        "part_family": "Hydraulics",
                        "quantity_available": 0,
                        "reorder_point": 44,
                        "criticality": "High",
                    }
                ],
            }

        On error, ``{"status": "error", "message": <details>}``.
    """
    try:
        with engine.connect() as conn:
            params = {'site_id': site_id, 'open_status': 'open'}

            # Site metadata. `mappings().first()` gives a dict-like single row
            # or None if no site matches.
            site = conn.execute(
                text("""
                    SELECT
                        site_id,
                        site_name,
                        site_region,
                        site_type,
                        site_mission_priority AS mission_priority
                    FROM sites
                    WHERE site_id = :site_id
                """),
                params,
            ).mappings().first()

            if site is None:
                return {
                    'status': 'error',
                    'message': f'Site {site_id!r} not found',
                }

            # All four aggregate queries below use SUM(CASE WHEN ...) so the
            # result is always a single row (even when the site has zero
            # inventory / shipments / maintenance events).
            inventory = conn.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_inventory_positions,
                        COALESCE(SUM(CASE WHEN stockout_flag THEN 1 ELSE 0 END), 0)
                            AS stockout_count,
                        COALESCE(SUM(CASE WHEN below_reorder_point THEN 1 ELSE 0 END), 0)
                            AS below_reorder_count,
                        COALESCE(SUM(CASE WHEN below_safety_stock THEN 1 ELSE 0 END), 0)
                            AS below_safety_stock_count
                    FROM inventory_positions
                    WHERE site_id = :site_id
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
                    WHERE site_id = :site_id
                """),
                params,
            ).mappings().first()

            maintenance = conn.execute(
                text("""
                    SELECT
                        COALESCE(SUM(CASE WHEN status = :open_status THEN 1 ELSE 0 END), 0)
                            AS open_maintenance_events,
                        AVG(CASE WHEN status = :open_status THEN backlog_days END)
                            AS average_backlog_days,
                        COALESCE(SUM(days_non_mission_capable), 0)
                            AS total_days_non_mission_capable
                    FROM maintenance_events
                    WHERE site_id = :site_id
                """),
                params,
            ).mappings().first()

            # Top 5 most starved parts at this site, joined with part_master
            # for descriptive columns. "Most starved" = biggest shortfall
            # vs. reorder point (negative diffs first).
            top_parts = conn.execute(
                text("""
                    SELECT
                        p.part_id,
                        p.part_name,
                        p.part_family,
                        i.quantity_available,
                        i.reorder_point,
                        p.criticality
                    FROM inventory_positions i
                    JOIN part_master p ON p.part_id = i.part_id
                    WHERE i.site_id = :site_id
                    ORDER BY (i.quantity_available - i.reorder_point) ASC
                    LIMIT 5
                """),
                params,
            ).mappings().all()

        total_shipments = int(shipments['total_shipments'])
        delayed_shipments = int(shipments['delayed_shipments'])
        delayed_rate = (
            delayed_shipments / total_shipments if total_shipments > 0 else 0
        )

        return {
            'status': 'ok',
            'site': dict(site),
            'inventory': {
                'total_inventory_positions': int(inventory['total_inventory_positions']),
                'stockout_count': int(inventory['stockout_count']),
                'below_reorder_count': int(inventory['below_reorder_count']),
                'below_safety_stock_count': int(inventory['below_safety_stock_count']),
            },
            'shipments': {
                'total_shipments': total_shipments,
                'delayed_shipments': delayed_shipments,
                'delayed_shipment_rate': round(delayed_rate, 4),
                # `or 0` covers the AVG-over-zero-rows case (returns NULL).
                'average_delay_days': round(float(shipments['average_delay_days'] or 0), 2),
            },
            'maintenance': {
                'open_maintenance_events': int(maintenance['open_maintenance_events']),
                'average_backlog_days': round(float(maintenance['average_backlog_days'] or 0), 2),
                'total_days_non_mission_capable': int(maintenance['total_days_non_mission_capable']),
            },
            'top_constrained_parts': [dict(p) for p in top_parts],
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
        }