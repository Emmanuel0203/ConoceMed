"""
Tests para `views/vistaInicio.py`.

Los tests verifican que la ruta `/inicio` responde correctamente y que
el blueprint puede renderizar la página con datos suministrados por un
`APIClient` simulado. Documentado en español.
"""
import os
import importlib.util
from flask import Flask
from types import SimpleNamespace
import jinja2
from types import SimpleNamespace


class DummyAPIClient:
    def __init__(self, resource):
        self.resource = resource

    def get_data(self):
        if self.resource == "Localidad":
            return {"datos": [{"idLocalidad": 1, "nombre": "Loc1"}]}
        if self.resource == "Sitios":
            return [{"idSitio": "1", "estado": "Pendiente"}, {"idSitio": "2", "estado": "Aprobado"}]
        return []


def load_module(filename):
    # Importar el módulo tal como lo hace la aplicación (paquete `views`) para
    # que los monkeypatch afecten al blueprint registrado en `main.app`.
    mod_name = filename[:-3]
    return importlib.import_module(f'views.{mod_name}')


def test_home_get(client, monkeypatch):
    """Comprueba que GET /inicio devuelve 200 (renderiza la página de inicio)."""
    vista = load_module('vistaInicio.py')
    # parchear el módulo real usado por la app
    monkeypatch.setattr(vista, 'APIClient', DummyAPIClient)
    # En main.py el blueprint `vistaInicio` se registró con url_prefix='/inicio'
    # y la ruta dentro del blueprint también es '/inicio', por lo que la URL
    # completa es '/inicio/inicio'
    resp = client.get('/inicio/inicio')
    assert resp.status_code == 200
