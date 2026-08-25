from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine
from utils.create_session import clear_session_cookie

router = APIRouter(prefix='/api/logout', tags=['Logout'])


@router.post('/')
async def logout(request: Request, response: Response, engine: Engine = Depends(get_engine),):
    """Logout the current user."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(status_code=401, detail='Unauthorized')
    with engine.connect() as conn:
        conn.execute(
            text('DELETE FROM sessions WHERE id = :session_id'),
            {'session_id': session_id},
        )
        conn.commit()
    clear_session_cookie(response)
    return {'message': 'Logged out successfully'}
