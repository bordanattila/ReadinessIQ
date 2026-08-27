"""Unit tests for `integrations.site_client.SiteClient`."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.integrations import site_client


def test_raises_when_base_url_is_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(site_client, 'PROJECT_ROOT', tmp_path)
    monkeypatch.delenv('CLIENT_BASE_URL', raising=False)

    with pytest.raises(ValueError, match='CLIENT_BASE_URL'):
        site_client.SiteClient()


def test_loads_base_url_from_env(monkeypatch, tmp_path):
    monkeypatch.setattr(site_client, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setenv('CLIENT_BASE_URL', 'http://simulator.test/')

    client = site_client.SiteClient()

    assert client.base_url == 'http://simulator.test'


def test_get_shipments_returns_shipments_list(monkeypatch, tmp_path):
    monkeypatch.setattr(site_client, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setenv('CLIENT_BASE_URL', 'http://simulator.test')

    expected_shipments = [
        {
            'shipment_id': 'SHIP-83921',
            'site_id': 'SITE-001',
            'part_id': 'PART-00491',
            'quantity_shipped': 15,
        }
    ]

    mock_response = MagicMock()
    mock_response.json.return_value = {
        'status': 'ok',
        'shipments': expected_shipments,
    }
    mock_http_client = MagicMock()
    mock_http_client.get.return_value = mock_response
    monkeypatch.setattr(
        site_client.httpx,
        'Client',
        lambda *args, **kwargs: mock_http_client,
    )

    client = site_client.SiteClient()
    shipments = client.get_shipments()

    mock_http_client.get.assert_called_once_with(
        'http://simulator.test/api/v1/shipments/'
    )
    assert shipments == expected_shipments
