from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine

router = APIRouter(prefix='/api/kpis', tags=['KPIs'])

@router.get('/overview')
async def get_kpi_overview(engine: Engine = Depends(get_engine)):
    try:
        with engine.connect() as conn:
            total_inventory_rows = conn.execute(
                text('SELECT COUNT(*) FROM inventory_positions')
                ).scalar()

            stockout_count = conn.execute(
                text('SELECT COUNT(*) FROM inventory_positions WHERE stockout_flag = True')
                ).scalar()
            
            below_reorder_point_count = conn.execute(
                text('SELECT COUNT(*) FROM inventory_positions WHERE below_reorder_point = True')
                ).scalar()
            
            below_safety_stock_count = conn.execute(
                text('SELECT COUNT(*) FROM inventory_positions WHERE below_safety_stock = True')
                ).scalar()
            
            total_shipments_count = conn.execute(
                text('SELECT COUNT(*) FROM shipments')
                ).scalar()

            delayed_shipments_count = conn.execute(
                text('SELECT COUNT(*) FROM shipments WHERE delayed_flag = True')
                ).scalar()
                
            average_delay_days = conn.execute(
                text('SELECT AVG(delay_days) FROM shipments WHERE delayed_flag = True')
                ).scalar()

            # Use bind parameter (:status) instead of string interpolation to
            # prevent SQL injection — SQLAlchemy escapes the value safely.
            open_maintenance_events_count = conn.execute(
                text('SELECT COUNT(*) FROM maintenance_events WHERE status = :status'),
                {'status': 'open'},
                ).scalar()

            average_backlog_days = conn.execute(
                text('SELECT AVG(backlog_days) FROM maintenance_events WHERE status = :status'),
                {'status': 'open'},
                ).scalar()

        stockout_rate = (
            stockout_count / total_inventory_rows
            if total_inventory_rows > 0 else 0
        )        
        below_safety_stock_rate = (
            below_safety_stock_count / total_inventory_rows
            if total_inventory_rows > 0 else 0
        )
        below_reorder_rate = (
            below_reorder_point_count / total_inventory_rows
            if total_inventory_rows
            else 0
        )
        delayed_shipments_rate = (
            delayed_shipments_count / total_shipments_count
            if total_shipments_count > 0 else 0
        )
        
        return {
            'status': 'ok',
            'inventory': {
                'total_inventory_positions': total_inventory_rows,
                'stockout_count': stockout_count,
                'stockout_rate': round(stockout_rate, 4),
                'below_reorder_count': below_reorder_point_count,
                'below_reorder_rate': round(below_reorder_rate, 4),
            },
            'shipments': {
                'total_shipments': total_shipments_count,
                'delayed_shipments': delayed_shipments_count,
                'delayed_shipment_rate': round(delayed_shipments_rate, 4),
                'average_delay_days': round(float(average_delay_days or 0), 2),
            },
            'maintenance': {
                'open_maintenance_events': open_maintenance_events_count,
                'average_backlog_days': round(float(average_backlog_days or 0), 2),
            },
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            }