from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine

router = APIRouter()


@router.get('/health')
async def health_check(engine: Engine = Depends(get_engine)):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            return {
                'status': 'ok',
                'database': 'connected',
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'database': 'disconnected',
        }
