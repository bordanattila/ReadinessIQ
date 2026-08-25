from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine
from app.models.user import UserCreate
from utils.create_session import create_session_id, insert_session, set_session_cookie
from utils.password import generate_salt, hash_password_with_salt

router = APIRouter(prefix='/api/register_user', tags=['Register User'])


@router.post('/')
async def register_user(
    user: UserCreate,
    response: Response,
    engine: Engine = Depends(get_engine),
):
    """Register a new user. Password is hashed before storage."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text('SELECT 1 FROM users WHERE email = :email'),
                {'email': user.email},
            )
            if result.fetchone() is not None:
                raise HTTPException(status_code=400, detail='Email already exists')

            salt = generate_salt()
            hashed_password = hash_password_with_salt(user.password, salt)
            insert_result = conn.execute(
                text(
                    'INSERT INTO users (name, email, password) '
                    'VALUES (:name, :email, :password) '
                    'RETURNING id'
                ),
                {'name': user.name, 'email': user.email, 'password': hashed_password},
            )
            registered_user_id = insert_result.fetchone().id

            session_id = create_session_id()
            insert_session(conn, session_id, registered_user_id)
            conn.commit()
            set_session_cookie(response, session_id)
            return {'message': 'User registered successfully'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
