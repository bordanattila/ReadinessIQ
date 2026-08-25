"""Tests for MFA setup and verification endpoints."""

import pyotp
from sqlalchemy import text

REGISTER_URL = '/api/register_user/'
LOGIN_URL = '/api/login/'
MFA_SETUP_URL = '/api/mfa/setup/'
MFA_VERIFY_URL = '/api/mfa/verify/'
ME_URL = '/api/me/'


def _register(client, email='test@test.com', password='test'):
    return client.post(
        REGISTER_URL,
        json={'name': 'test', 'email': email, 'password': password},
    )


def _login(client, email='test@test.com', password='test'):
    return client.post(
        LOGIN_URL,
        json={'email': email, 'password': password},
    )


def _enable_mfa_for_user(engine, email='test@test.com'):
    secret = pyotp.random_base32()
    with engine.connect() as conn:
        conn.execute(
            text(
                'UPDATE users SET mfa_enabled = true, mfa_secret = :secret '
                'WHERE email = :email'
            ),
            {'secret': secret, 'email': email},
        )
        conn.commit()
    return secret


def test_mfa_setup_returns_provisioning_uri(client_factory, users_engine):
    client = client_factory(users_engine)
    _register(client)

    response = client.get(MFA_SETUP_URL)

    assert response.status_code == 200
    body = response.json()
    assert body['otpauth_url'].startswith('otpauth://totp/')
    assert len(body['secret']) >= 16


def test_mfa_verify_enables_account_and_marks_session_verified(client_factory, users_engine):
    client = client_factory(users_engine)
    _register(client)

    setup = client.get(MFA_SETUP_URL).json()
    secret = setup['secret']
    code = pyotp.TOTP(secret).now()

    response = client.post(MFA_VERIFY_URL, json={'code': code})

    assert response.status_code == 200
    assert response.json() == {'message': 'MFA verified successfully'}

    me = client.get(ME_URL).json()
    assert me['mfa_enabled'] is True
    assert me['mfa_verified'] is True


def test_login_for_mfa_user_requires_verification(client_factory, users_engine):
    client = client_factory(users_engine)
    _register(client)
    secret = _enable_mfa_for_user(users_engine)

    _login(client)
    me = client.get(ME_URL).json()

    assert me['mfa_enabled'] is True
    assert me['mfa_verified'] is False

    code = pyotp.TOTP(secret).now()
    client.post(MFA_VERIFY_URL, json={'code': code})
    me_after = client.get(ME_URL).json()
    assert me_after['mfa_verified'] is True


def test_fresh_login_allows_dashboard_without_mfa(client_factory, users_engine):
    client = client_factory(users_engine)
    _register(client)

    _login(client)
    me = client.get(ME_URL).json()

    assert me['mfa_enabled'] is False
    assert me['mfa_verified'] is True


def test_mfa_verify_rejects_invalid_code(client_factory, users_engine):
    client = client_factory(users_engine)
    _register(client)
    client.get(MFA_SETUP_URL)

    response = client.post(MFA_VERIFY_URL, json={'code': '000000'})

    assert response.status_code == 401
    assert response.json() == {'detail': 'Invalid MFA code'}
