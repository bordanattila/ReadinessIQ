"""Tests for the /api/login endpoint.

Uses an in-memory SQLite engine via the `users_engine` fixture in conftest.py.
"""

REGISTER_URL = "/api/register_user/"
LOGIN_URL = "/api/login/"


def _register(client, email="test@test.com", password="test"):
    return client.post(
        REGISTER_URL,
        json={"name": "test", "email": email, "password": password},
    )


def test_login_status_ok(client_factory, users_engine):
    client = client_factory(users_engine)
    _register(client)

    response = client.post(
        LOGIN_URL,
        json={"email": "test@test.com", "password": "test"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}


def test_login_invalid_password_credentials(client_factory, users_engine):
    client = client_factory(users_engine)
    _register(client, password="test")

    response = client.post(
        LOGIN_URL,
        json={"email": "test@test.com", "password": "wrong_password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_login_invalid_email_credentials(client_factory, users_engine):
    client = client_factory(users_engine)
    _register(client)

    response = client.post(
        LOGIN_URL,
        json={"email": "wrong_email@test.com", "password": "test"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
