from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine
from app.models.user import UserLogin
from utils.password import verify_password_with_salt

router = APIRouter(prefix='/api/login', tags=['Login'])

@router.post('/')
async def login(excisting_user: UserLogin, engine: Engine = Depends(get_engine)):
    try:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT * FROM users WHERE email = :email'), {'email': excisting_user.email})
            existing_user = result.fetchone()

            if existing_user is None:
                raise HTTPException(status_code=401, detail='Invalid credentials')
            if not verify_password_with_salt(excisting_user.password, existing_user.password):
                raise HTTPException(status_code=401, detail='Invalid credentials')
            return {'message': 'Login successful'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))