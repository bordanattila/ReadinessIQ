"""Readiness root-cause overview (MVP heuristics).

Each category counts independent *signals* (rows) from operational tables so
the story is easy to explain, not a perfect causal attribution.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine

router = APIRouter(prefix='/api/root-cause', tags=['Root cause'])

_SCORING_NOTE = (
    'relative_severity_score is normalized against the highest root-cause '
    'signal count in the current result set.'
)

# (category_id, summary_field, display_name, explanation)
_READINESS_RISK_CATEGORIES: tuple[tuple[str, str, str, str], ...] = (
    (
        'supplier_delay',
        'supplier_delay_signals',
        'Supplier delay',
        'Shipments arrived after the expected delivery window, extending site lead time.',
    ),
    (
        'reactive_site_ordering',
        'reactive_site_order_signals',
        'Reactive site ordering',
        'Purchase order was created after an inventory snapshot already showed this '
        'site and part below reorder or safety stock (reactive ordering; MVP).',
    ),
    (
        'inventory_policy_risk',
        'inventory_policy_signals',
        'Inventory policy risk',
        'Parts are below reorder point or safety stock, suggesting replenishment thresholds may be insufficient.',
    ),
    (
        'maintenance_demand',
        'maintenance_demand_signals',
        'Maintenance demand',
        'Open or deferred maintenance work indicates elevated sustainment load affecting readiness.',
    ),
)

_READINESS_RISK_SQL = """
SELECT
    (SELECT COALESCE(SUM(CASE WHEN delayed_flag THEN 1 ELSE 0 END), 0) FROM shipments)
        AS supplier_delay_signals,
    (SELECT COUNT(DISTINCT o.order_id) FROM supplier_orders o
     WHERE EXISTS (
         SELECT 1 FROM inventory_positions i
         WHERE i.site_id = o.site_id
           AND i.part_id = o.order_part_id
           AND (
               i.below_reorder_point OR i.below_safety_stock OR i.stockout_flag
           )
           AND substr(cast(o.order_created_at AS text), 1, 10)
               > substr(cast(i.snapshot_date AS text), 1, 10)
     )) AS reactive_site_order_signals,
    (SELECT COALESCE(SUM(CASE WHEN below_reorder_point OR below_safety_stock THEN 1 ELSE 0 END), 0)
        FROM inventory_positions) AS inventory_policy_signals,
    (SELECT COUNT(*) FROM maintenance_events
     WHERE status IN ('open', 'in_progress', 'awaiting_parts', 'deferred'))
        AS maintenance_demand_signals
"""


def _int_scalar(value: object) -> int:
    if value is None:
        return 0
    return int(value)


@router.get('/readiness-risk')
def get_readiness_root_cause(engine: Engine = Depends(get_engine)):
    """Summarize what is driving readiness risk (MVP signal counts).

    Four buckets: supplier delays, reactive site ordering (PO after stressed
    inventory snapshot), inventory threshold stress, and active maintenance demand.
    Counts are additive row
    tallies across tables, not mutually exclusive causal shares.
    """
    try:
        with engine.connect() as conn:
            row = conn.execute(text(_READINESS_RISK_SQL)).mappings().one()

        counts: dict[str, int] = {}
        for cat_id, summary_key, _label, _expl in _READINESS_RISK_CATEGORIES:
            counts[cat_id] = _int_scalar(row[summary_key])

        total = sum(counts.values())
        max_count = max(counts.values()) if counts else 0

        summary: dict[str, object] = {
            'total_risk_signals': total,
            'supplier_delay_signals': counts['supplier_delay'],
            'reactive_site_order_signals': counts['reactive_site_ordering'],
            'inventory_policy_signals': counts['inventory_policy_risk'],
            'maintenance_demand_signals': counts['maintenance_demand'],
        }

        if total == 0:
            summary['primary_root_cause'] = 'Insufficient data'
            root_causes: list[dict[str, object]] = []
            for cat_id, _sk, display, explanation in _READINESS_RISK_CATEGORIES:
                root_causes.append(
                    {
                        'root_cause': display,
                        'signal_count': 0,
                        'share_of_total': 0.0,
                        'relative_severity_score': 0.0,
                        'explanation': explanation,
                    }
                )
            return {
                'status': 'ok',
                'scoring_note': _SCORING_NOTE,
                'summary': summary,
                'root_causes': root_causes,
            }

        # Primary driver: largest count; ties broken by category order above.
        ordered = sorted(
            _READINESS_RISK_CATEGORIES,
            key=lambda c: (-counts[c[0]], _READINESS_RISK_CATEGORIES.index(c)),
        )
        summary['primary_root_cause'] = ordered[0][2]

        max_for_severity = max_count if max_count > 0 else 1
        root_causes = []
        for cat_id, _sk, display, explanation in _READINESS_RISK_CATEGORIES:
            n = counts[cat_id]
            share = round(n / total, 3) if total else 0.0
            severity = round(100.0 * n / max_for_severity, 1)
            root_causes.append(
                {
                    'root_cause': display,
                    'signal_count': n,
                    'share_of_total': share,
                    'relative_severity_score': severity,
                    'explanation': explanation,
                }
            )

        root_causes.sort(key=lambda r: (-int(r['signal_count']), r['root_cause']))

        return {
            'status': 'ok',
            'scoring_note': _SCORING_NOTE,
            'summary': summary,
            'root_causes': root_causes,
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
        }
