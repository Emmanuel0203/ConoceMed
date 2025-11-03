import os
import requests
import pytest
import allure

from utils.api_client import APIClient


def test_get_data_handles_missing_env(monkeypatch):
    """Prueba unitaria: APIClient debe lanzar ValueError si API_URL no está configurada."""
    monkeypatch.setenv('API_URL', '')
    with pytest.raises(ValueError):
        APIClient('Usuario')


@allure.feature("Utils")
def test_make_request_get_ok(monkeypatch):
    """Prueba de integración: _make_request devuelve JSON parseado para status 200."""
    monkeypatch.setenv('API_URL', 'http://mi-api-prueba/api')

    class DummyResp:
        status_code = 200
        content = b'{"datos": []}'
        def json(self):
            return {"datos": []}

    def fake_get(url, params=None, timeout=None):
        return DummyResp()

    monkeypatch.setattr(requests, 'get', fake_get)
    client = APIClient('Usuario')
    data = client.get_data()
    assert isinstance(data, list)
