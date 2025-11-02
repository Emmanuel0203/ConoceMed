"""
Tests para `views/vistaSitio.py`.

Verificamos que la ruta `/sitios` renderiza correctamente cuando la función
`obtener_sitios` devuelve datos esperados (mock simple).
"""
import os
import importlib.util
from flask import Flask
import jinja2
from types import SimpleNamespace


def load_module(filename):
    mod_name = filename[:-3]
    return importlib.import_module(f'views.{mod_name}')


def test_listar_sitios(client, monkeypatch):
    """Comprueba que GET /sitios devuelve 200 y usa datos simulados."""
    vista = load_module('vistaSitio.py')

    # mockear obtener_sitios en el módulo de la vista
    monkeypatch.setattr(vista, 'obtener_sitios', lambda: [{'idSitio': '1', 'nombre': 'A'}])

    # En main.py el blueprint vistaSitio se registró con url_prefix='/sitios'
    # y la ruta dentro del blueprint es '/sitios' => '/sitios/sitios'
    resp = client.get('/sitios/sitios')
    assert resp.status_code == 200
