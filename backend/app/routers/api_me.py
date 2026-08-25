from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine

router = APIRouter(prefix='/api/me', tags=['Me'])


@router.get('/')
async def get_current_user(request: Request, engine: Engine = Depends(get_engine)):
    """Get the current user from the session cookie."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(status_code=401, detail='Unauthorized')
    with engine.connect() as conn:
        result = conn.execute(
            text('SELECT * FROM sessions WHERE id = :session_id'),
            {'session_id': session_id},
        )
        session = result.fetchone()
        if session is None:
            raise HTTPException(status_code=401, detail='Unauthorized')
        if session.expires_at <= datetime.now():
            raise HTTPException(status_code=401, detail='Session expired')

        result = conn.execute(
            text('SELECT * FROM users WHERE id = :user_id'),
            {'user_id': session.user_id},
        )
        user = result.fetchone()
        if user is None:
            raise HTTPException(status_code=401, detail='Unauthorized')

    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
    }
