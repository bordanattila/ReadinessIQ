import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import get_engine
from utils.mfa_auth import pyotp_verify
from utils.session_auth import get_session_user

router = APIRouter(prefix='/api/mfa', tags=['MFA'])


class MfaVerifyRequest(BaseModel):
    code: str


@router.get('/setup/')
async def mfa_setup(request: Request, engine: Engine = Depends(get_engine)):
    """Return a provisioning URI for enrolling an authenticator app."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(status_code=401, detail='Unauthorized')

    with engine.connect() as conn:
        _, user = get_session_user(conn, session_id)
        if user.mfa_enabled:
            raise HTTPException(status_code=400, detail='MFA already enabled')

        secret = user.mfa_secret or pyotp.random_base32()
        if not user.mfa_secret:
            conn.execute(
                text('UPDATE users SET mfa_secret = :secret WHERE id = :user_id'),
                {'secret': secret, 'user_id': user.id},
            )
            conn.commit()

        totp = pyotp.TOTP(secret)
        otpauth_url = totp.provisioning_uri(name=user.email, issuer_name='ReadinessIQ')
        return {'otpauth_url': otpauth_url, 'secret': secret}


@router.post('/verify/')
async def mfa_verify(
    payload: MfaVerifyRequest,
    request: Request,
    engine: Engine = Depends(get_engine),
):
    """Verify a TOTP code and mark the current session as MFA-verified."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(status_code=401, detail='Unauthorized')

    with engine.connect() as conn:
        session, user = get_session_user(conn, session_id)
        if not user.mfa_secret:
            raise HTTPException(status_code=400, detail='MFA is not set up for this account')

        if not pyotp_verify(payload.code, user.mfa_secret):
            raise HTTPException(status_code=401, detail='Invalid MFA code')

        conn.execute(
            text('UPDATE users SET mfa_enabled = true WHERE id = :user_id'),
            {'user_id': user.id},
        )
        conn.execute(
            text('UPDATE sessions SET mfa_verified = true WHERE id = :session_id'),
            {'session_id': session.id},
        )
        conn.commit()

    return {'message': 'MFA verified successfully'}
