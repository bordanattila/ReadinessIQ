from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine
from app.models.user import UserLogin
from utils.create_session import create_session_id, insert_session, set_session_cookie
from utils.password import verify_password_with_salt

router = APIRouter(prefix='/api/login', tags=['Login'])


@router.post('/')
async def login(excisting_user: UserLogin, response: Response, engine: Engine = Depends(get_engine),):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text('SELECT * FROM users WHERE email = :email'),
                {'email': excisting_user.email},
            )
            existing_user = result.fetchone()

            if existing_user is None:
                raise HTTPException(status_code=401, detail='Invalid credentials')
            if not verify_password_with_salt(excisting_user.password, existing_user.password):
                raise HTTPException(status_code=401, detail='Invalid credentials')

            session_id = create_session_id()
            mfa_enabled = bool(getattr(existing_user, 'mfa_enabled', False))
            insert_session(
                conn,
                session_id,
                existing_user.id,
                mfa_verified=not mfa_enabled,
            )
            conn.commit()
            set_session_cookie(response, session_id)
            return {'message': 'Login successful'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
