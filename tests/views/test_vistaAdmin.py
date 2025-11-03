"""
Tests para `views/vistaAdmin.py`.

Prueba mínima: comprobar que la ruta `/admin` responde correctamente.
La vista completa es compleja; aquí hacemos un test de humo (smoke test)
para la página del panel de administración.
"""
import os
import importlib.util
from flask import Flask
import io
import tempfile
import jinja2
from types import SimpleNamespace



def load_module(filename):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(root, 'views', filename)
    spec = importlib.util.spec_from_file_location(filename[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_admin_panel_get(client):
    """GET /admin debe devolver 200 (panel de administración)."""
    resp = client.get('/admin')
    assert resp.status_code == 200


def test_crear_lugar_post_with_file(client, monkeypatch):
    """Simula POST /admin/crear con un archivo y verifica que redirige tras crear.

    Se mockean dependencias externas (APIClient, build_payload_from_form, apply_geocode,
    allowed_file) para que el flujo principal proceda sin llamadas reales.
    """
    vista = load_module('vistaAdmin.py')

    # Mock de build_payload_from_form para devolver datos mínimos
    def fake_build_payload(form):
        return {
            'nombre': 'LugarPrueba',
            'direccion': 'Calle X',
            'fkidLocalidad': '1',
            'fkidCategoria_Turistica': '1'
        }

    monkeypatch.setattr(vista, 'build_payload_from_form', fake_build_payload)

    # Mock apply_geocode para no depender del servicio externo
    monkeypatch.setattr(vista, 'apply_geocode', lambda datos, api_client_factory=None: (None, None))

    # allowed_file debe aprobar el archivo
    monkeypatch.setattr(vista, 'allowed_file', lambda f: (True, None))

    # Fake APIClient con comportamiento necesario
    class FakeAPI:
        def __init__(self, resource):
            self.resource = resource

        def get_data(self):
            if self.resource == 'Localidad':
                return []
            if self.resource == 'Categoria_Turistica':
                return []
            return []

        def get_data_by_key(self, key, value):
            # Para validar creado_por
            if self.resource == 'Usuario':
                return {'datos': [{'idUsuario': value}]}
            return None

        def insert_data(self, json_data=None):
            if self.resource == 'Sitios':
                return {'success': True, 'idSitio': 'nuevo-id-123'}
            if self.resource == 'Multimedia':
                return {'estado': 200}
            return {}

    monkeypatch.setattr(vista, 'APIClient', FakeAPI)

    # Simular archivo enviado (conftest proporciona UPLOAD_FOLDER temporal)
    file_stream = io.BytesIO(b'contenido-imagen')
    file_stream.name = 'foto.png'
    data = {
        'nombre': 'LugarPrueba',
        'direccion': 'Calle X',
        'fkidLocalidad': '1',
        'fkidCategoria_Turistica': '1',
        'archivos': (file_stream, 'foto.png')
    }

    resp = client.post('/admin/crear', data=data, content_type='multipart/form-data')
    # la vista redirige tras crear correctamente
    assert resp.status_code in (301, 302)
