"""Helpers for server-side session storage and session cookies."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from fastapi import Response
from sqlalchemy import text
from sqlalchemy.engine import Connection

SESSION_COOKIE_NAME = 'session_id'
SESSION_MAX_AGE_SECONDS = 3600


def create_session_id() -> str:
    """Return a new opaque session identifier."""
    return str(uuid.uuid4())


def insert_session(conn: Connection, session_id: str, user_id: int, *, mfa_verified: bool = True, lifetime: timedelta = timedelta(hours=1)) -> None:
    """Insert a session row using the caller's open connection."""
    created_at = datetime.now()
    expires_at = created_at + lifetime
    conn.execute(
        text(
            'INSERT INTO sessions (id, user_id, created_at, expires_at, mfa_verified) '
            'VALUES (:session_id, :user_id, :created_at, :expires_at, :mfa_verified)'
        ),
        {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': created_at,
            'expires_at': expires_at,
            'mfa_verified': mfa_verified,
        },
    )


def set_session_cookie(response: Response, session_id: str) -> None:
    """Attach the session cookie to the outgoing response."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite='lax',
        secure=False,
        path='/',
    )


def clear_session_cookie(response: Response) -> None:
    """Remove the session cookie from the client."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, path='/')
