from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.engine import Connection, Row


def _as_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def get_session_user(conn: Connection, session_id: str) -> tuple[Row, Row]:
    result = conn.execute(
        text('SELECT * FROM sessions WHERE id = :session_id'),
        {'session_id': session_id},
    )
    session = result.fetchone()
    if session is None:
        raise HTTPException(status_code=401, detail='Unauthorized')
    if _as_datetime(session.expires_at) <= datetime.now():
        raise HTTPException(status_code=401, detail='Session expired')

    result = conn.execute(
        text('SELECT * FROM users WHERE id = :user_id'),
        {'user_id': session.user_id},
    )
    user = result.fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail='Unauthorized')
    return session, user
