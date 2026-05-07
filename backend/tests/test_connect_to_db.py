"""Unit tests for `utils.connect_to_db.get_database_url`."""

from __future__ import annotations

import pytest

from utils import connect_to_db


def test_returns_value_from_env(monkeypatch, tmp_path):
    """When DATABASE_URL is set in the environment, it's returned verbatim."""
    monkeypatch.setattr(connect_to_db, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test_db")

    assert (
        connect_to_db.get_database_url()
        == "postgresql://test:test@localhost/test_db"
    )


def test_loads_from_dotenv_when_env_is_unset(monkeypatch, tmp_path):
    """When DATABASE_URL is missing from the env, .env is consulted."""
    (tmp_path / ".env").write_text("DATABASE_URL=postgresql://from-dotenv/db\n")
    monkeypatch.setattr(connect_to_db, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert connect_to_db.get_database_url() == "postgresql://from-dotenv/db"


def test_dotenv_overrides_pre_existing_env(monkeypatch, tmp_path):
    """`override=True` means the .env value wins over a stale shell export.

    This is the bug we hit in development where a stale DATABASE_URL in the
    shell silently shadowed the .env file.
    """
    (tmp_path / ".env").write_text("DATABASE_URL=postgresql://from-dotenv/db\n")
    monkeypatch.setattr(connect_to_db, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("DATABASE_URL", "postgresql://stale-shell/db")

    assert connect_to_db.get_database_url() == "postgresql://from-dotenv/db"


def test_raises_when_url_is_missing(monkeypatch, tmp_path):
    """No env var, no .env entry -> a clear ValueError, not a None return."""
    monkeypatch.setattr(connect_to_db, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError, match="DATABASE_URL"):
        connect_to_db.get_database_url()
