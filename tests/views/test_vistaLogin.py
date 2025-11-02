"""
Tests para `views/vistaLogin.py`.

Se prueban el GET para mostrar la página de login y un POST simulado que
realiza un inicio de sesión exitoso. Se usa un formulario y autenticador
simulados para evitar dependencias externas.
"""
import os
import importlib.util
from flask import Flask
from types import SimpleNamespace
import jinja2
from types import SimpleNamespace


def load_module(filename):
    mod_name = filename[:-3]
    return importlib.import_module(f'views.{mod_name}')


class FakeForm:
    def __init__(self, correo=None, password=None):
        self.correo = type('o', (), {'data': correo})
        self.password = type('o', (), {'data': password})

    def validate_on_submit(self):
        return True


class FakeUser:
    def __init__(self):
        self.nombre = 'UsuarioPrueba'
        self.id = 'test-user-id'
        # atributos requeridos por flask-login
        self.is_active = True
        self.is_authenticated = True


def test_get_login(client, monkeypatch):
    """GET /login debe devolver la plantilla del formulario de login."""
    vista = load_module('vistaLogin.py')
    # En main.py el blueprint `vistaLogin` se registró con url_prefix='/login'
    # y la ruta dentro del blueprint también es '/login' => '/login/login'
    resp = client.get('/login/login')
    assert resp.status_code == 200


def test_post_login_success(client, monkeypatch):
    """Simula un POST de login exitoso y verifica que la vista intenta redirigir al índice.

    Observación: registramos una ruta `index` mínima para evitar errores al resolver la URL de redirección.
    """
    vista = load_module('vistaLogin.py')

    # sustituir LoginForm por nuestro FakeForm
    monkeypatch.setattr(vista, 'LoginForm', FakeForm)

    # sustituir la función de autenticación para forzar éxito
    def fake_auth(correo, password):
        return True, FakeUser()

    monkeypatch.setattr(vista, 'autenticar_usuario', fake_auth)

    # evitar dependencia en flask-login (login_manager) durante el test
    monkeypatch.setattr(vista, 'login_user', lambda user: None)

    # realizar POST contra la ruta real registrada en main
    resp = client.post('/login/login', data={'correo': 'a@b.c', 'password': 'x'})
    # se espera redirección tras login exitoso
    assert resp.status_code in (301, 302)
