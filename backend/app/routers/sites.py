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
