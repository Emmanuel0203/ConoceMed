"""
Tests para `views/vistaSugerido.py`.

Se prueban:
- GET /sugerir devuelve 200 cuando los recursos externos son válidos (APIClient simulado).
- GET /lugares devuelve JSON con la lista de lugares (simulado).

Documentados en español.
"""
import os
import json
import io
import jinja2
import importlib
import views.vistaSugerido as vista



class DummyAPIClient:
    def __init__(self, resource):
        self.resource = resource

    def get_data(self):
        if self.resource == 'Localidad':
            return [{'idLocalidad': 1, 'nombre': 'Loc1'}]
        if self.resource == 'Categoria_Turistica':
            return [{'idCategoria_Turistica': 1, 'nombre': 'Cat1'}]
        if self.resource == 'Sitios':
            return []
        return []


def test_get_sugerir(client, monkeypatch):
    """GET /sugerir debe devolver 200 con APIClient y formulario simulados."""
    # parchear el módulo real usado por la app
    monkeypatch.setattr(vista, 'APIClient', DummyAPIClient)

    # sustituir el formulario por uno simple que no valide al hacer POST
    class FakeForm:
        def __init__(self):
            self.idLocalidad = type('o', (), {'choices': []})
            self.idCategoria_Turistica = type('o', (), {'choices': []})

        def validate_on_submit(self):
            return False

    monkeypatch.setattr(vista, 'LugarSugeridoForm', FakeForm)

    resp = client.get('/sugerir')
    assert resp.status_code == 200


def test_get_lugares_json(client, monkeypatch):
    """GET /lugares debe devolver JSON con la lista de lugares usando APIClient simulado."""
    # usar el módulo real
    # vista ya importado arriba
    class ClientList(DummyAPIClient):
        def get_data(self):
            return [{'idSitio': '1', 'nombre': 'X'}]

    monkeypatch.setattr(vista, 'APIClient', lambda resource: ClientList(resource))

    resp = client.get('/lugares')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)


def test_post_sugerir_success(client, monkeypatch):
    """Simula un POST /sugerir con un archivo y verifica respuesta success=True."""
    # parchear en el módulo real

    # Formulario falso que toma valores desde request.form
    class FakeFormPost:
        def __init__(self):
            # valores que la vista espera leer vía form.field.data
            self.nombre = type('o', (), {'data': 'NombrePrueba'})
            self.direccion = type('o', (), {'data': 'Direc'})
            self.descripcion = type('o', (), {'data': 'Desc'})
            self.latitud = type('o', (), {'data': '1.23'})
            self.longitud = type('o', (), {'data': '4.56'})
            self.horario_apertura = type('o', (), {'data': None})
            self.horario_cierre = type('o', (), {'data': None})
            self.tarifa = type('o', (), {'data': None})
            # usar strings para que coincida con los datos enviados en el form multipart
            self.idLocalidad = type('o', (), {'data': '1'})
            self.idCategoria_Turistica = type('o', (), {'data': '1'})

        def validate_on_submit(self):
            return True

    monkeypatch.setattr(vista, 'LugarSugeridoForm', FakeFormPost)

    # APIClient simulado para Sitios y Multimedia
    class FakeAPI:
        def __init__(self, resource):
            self.resource = resource

        def insert_data(self, json_data=None):
            if self.resource == 'Sitios':
                return {'success': True, 'idSitio': json_data.get('idSitio')}
            if self.resource == 'Multimedia':
                return {'success': True, 'idMultimedia': 'mm-1'}
            return {}

        def get_data(self):
            if self.resource == 'Localidad':
                return [{'idLocalidad': 1, 'nombre': 'Loc1'}]
            if self.resource == 'Categoria_Turistica':
                return [{'idCategoria_Turistica': 1, 'nombre': 'Cat1'}]
            return []

    monkeypatch.setattr(vista, 'APIClient', FakeAPI)

    # conftest.provee tmp_upload_dir y app/client fixtures; solo usar client

    # Simular archivo enviado
    data = {
        'nombre': 'NombrePrueba',
        'direccion': 'Direc',
        'descripcion': 'Desc',
        'latitud': '1.23',
        'longitud': '4.56',
        'idLocalidad': '1',
        'idCategoria_Turistica': '1'
    }
    file_stream = io.BytesIO(b'test-image-bytes')
    file_stream.name = 'foto.jpg'
    multipart = {
        **data,
        'archivos': (file_stream, 'foto.jpg')
    }

    resp = client.post('/sugerir', data=multipart, content_type='multipart/form-data')
    assert resp.status_code == 200
    j = json.loads(resp.data)
    assert j.get('success') is True
