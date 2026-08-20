"""Tests for the /api/register_user endpoint.

Uses an in-memory SQLite engine via the `users_engine` fixture in conftest.py.
"""


def test_register_user_status_ok(client_factory, users_engine):
    client = client_factory(users_engine)

    response = client.post(
        "/api/register_user/",
        json={"name": "test", "email": "test@test.com", "password": "test"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}


def test_register_user_duplicate_email(client_factory, users_engine):
    client = client_factory(users_engine)
    payload = {"name": "test", "email": "test@test.com", "password": "test"}

    assert client.post("/api/register_user/", json=payload).status_code == 200

    response = client.post("/api/register_user/", json=payload)

    assert response.status_code == 400
    assert response.json() == {"detail": "Email already exists"}


def test_register_user_invalid_data(client_factory, users_engine):
    client = client_factory(users_engine)

    response = client.post(
        "/api/register_user/",
        json={"name": "test", "password": "test"},
    )

    assert response.status_code == 422
