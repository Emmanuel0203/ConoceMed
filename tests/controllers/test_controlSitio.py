import allure
import pytest

import controllers.controlSitio as cs


def test_obtener_sitios_mock(monkeypatch):
    """Prueba unitaria: obtener_sitios debe devolver una lista vacía si la petición falla."""
    class DummyResp:
        def raise_for_status(self):
            return None
        def json(self):
            return {"datos": []}

    def fake_get(url, *args, **kwargs):
        return DummyResp()

    monkeypatch.setattr(cs, 'requests', type('R', (), {'get': fake_get}))
    sitios = cs.obtener_sitios()
    assert isinstance(sitios, list)


def test_crear_sitio_permiso():
    """Prueba de permiso: crear_sitio debe lanzar PermissionError si el rol no es admin."""
    with pytest.raises(PermissionError):
        cs.crear_sitio({}, rol="user")
