from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.engine import Engine

from app.db import get_engine
from utils.session_auth import get_session_user

router = APIRouter(prefix='/api/me', tags=['Me'])


@router.get('/')
async def get_current_user(request: Request, engine: Engine = Depends(get_engine)):
    """Get the current user from the session cookie."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(status_code=401, detail='Unauthorized')

    with engine.connect() as conn:
        session, user = get_session_user(conn, session_id)

    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'mfa_verified': bool(session.mfa_verified),
        'mfa_enabled': bool(getattr(user, 'mfa_enabled', False)),
    }
