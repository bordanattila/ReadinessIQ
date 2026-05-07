from sqlalchemy import create_engine

from app.db import get_engine
from app.main import app


def test_health_returns_ok_when_db_reachable(client_factory, empty_engine):
    client = client_factory(empty_engine)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_health_reports_disconnected_when_engine_is_broken(client_factory):
    # An engine pointed at a non-existent SQLite file path that we can't open
    # would still create a DB. Use an explicitly broken URL instead.
    broken = create_engine("sqlite:////nonexistent/dir/forbidden.db")
    client = client_factory(broken)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["database"] == "disconnected"
    assert "message" in body
