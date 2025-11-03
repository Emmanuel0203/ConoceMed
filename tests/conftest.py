import os
import sys
import pytest
import jinja2
from types import SimpleNamespace
import shutil

# Allure is optional in local developer environments. If not installed, provide a
# lightweight shim so tests can still run without the real `allure` package.
try:
    import allure
except Exception:
    class _AllureShim:
        def step(self, *a, **k):
            def _decorator(f):
                return f
            return _decorator

        def feature(self, *a, **k):
            def _decorator(f):
                return f
            return _decorator

        def story(self, *a, **k):
            def _decorator(f):
                return f
            return _decorator

        def severity(self, *a, **k):
            def _decorator(f):
                return f
            return _decorator

    allure = _AllureShim()

# Asegurar que el directorio raíz del proyecto esté en sys.path para que 'main' sea importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Importar la app Flask desde main
from main import app as flask_app
import utils.api_client as api_client_mod

@pytest.fixture
def app():
    """Proveer la aplicación Flask para pruebas (contexto de aplicación)."""
    # Ajustes de configuración útiles para pruebas: desactivar CSRF y activar TESTING
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['TESTING'] = True
    # clave secreta requerida por session/flash/CSRF internamente
    flask_app.secret_key = flask_app.config.get('SECRET_KEY', 'test-secret')

    # Proveer plantillas mínimas para evitar errores si las pruebas no cargan templates reales
    templates = {
        'base.html': 'base',
        'index.html': 'index',
        'login.html': 'login',
        'seccion4.html': 's4',
        'seccion7.html': 's7',
        'sitios.html': 'sitios',
        'crear_lugar.html': 'crear',
        'editar_lugar.html': 'editar',
        'editar_no_encontrado.html': 'noencontrado',
        'lugares_sugeridos.html': 'lugares',
        'uploads_list.html': 'uploads',
        '403.html': '403'
    }
    flask_app.jinja_loader = jinja2.DictLoader(templates)

    # asegurar current_user disponible en plantillas (evita jinja UndefinedError)
    # Registrar context_processor solo si la app no ha manejado ya una request
    if not getattr(flask_app, '_got_first_request', False):
        flask_app.context_processor(lambda: {'current_user': SimpleNamespace(is_authenticated=False)})
    else:
        # Si la app ya procesó una request (poco común en tests), inyectar
        # current_user como variable global de Jinja para evitar errores.
        try:
            flask_app.jinja_env.globals['current_user'] = SimpleNamespace(is_authenticated=False)
        except Exception:
            pass
    yield flask_app


@pytest.fixture(autouse=True)
def tmp_upload_dir(app, tmp_path):
    """Crear y configurar una carpeta temporal para uploads durante cada test.

    Esto evita que los tests escriban en el árbol del proyecto y proporciona
    un punto donde limpiar archivos creados durante la prueba.
    """
    d = tmp_path / 'uploads'
    d.mkdir()
    app.config['UPLOAD_FOLDER'] = str(d)
    yield d
    # intento de limpieza (si algo quedó)
    try:
        shutil.rmtree(str(d))
    except Exception:
        pass

@pytest.fixture
def client(app):
    """Cliente de prueba para realizar requests a la app."""
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_api(monkeypatch):
    """Fixture automática que reemplaza APIClient por un stub para evitar llamadas externas.

    Devuelve datos mínimos para que las vistas y formularios se puedan renderizar sin acceder
    a la API real.
    """
    class DummyAPI:
        def __init__(self, table_name):
            self.table_name = table_name

        def get_data(self, **kwargs):
            if self.table_name == "Localidad":
                return [{"idLocalidad": "1", "nombre": "Localidad de prueba"}]
            if self.table_name == "Categoria_Turistica":
                return [{"idCategoria_Turistica": "1", "nombre": "Categoría prueba"}]
            if self.table_name == "Sitios":
                return []
            return []

        def get_data_by_id(self, record_id):
            return {"datos": [{"idUsuario": "u1", "nombre": "Usuario prueba"}]}

        def get_data_by_key(self, key_name, key_value):
            return {"datos": [{"idUsuario": "u1", "nombre": "Usuario prueba"}]}

        def insert_data(self, json_data=None, files=None):
            return {"success": True, "datos": json_data}

        def update_data(self, record_id, json_data=None):
            return {"success": True, "datos": json_data}

        def delete_data(self, record_id):
            return {"success": True}

    monkeypatch.setattr(api_client_mod, "APIClient", DummyAPI)
    yield


# ----------------- Allure helpers and hooks -----------------
@pytest.fixture
def allure_step():
    """Helper para usar pasos de Allure desde tests.

    Uso:
        with allure_step('descripción'):
            ...
    """
    return allure.step


@pytest.fixture(scope='session', autouse=True)
def _allure_environment():
    """Escribe un `environment.properties` en `allure-results/` para enriquecer el reporte.

    Esto no falla si Allure no está instalado — es seguro en entornos locales.
    """
    try:
        ar = os.path.join(os.getcwd(), 'allure-results')
        os.makedirs(ar, exist_ok=True)
        envf = os.path.join(ar, 'environment.properties')
        with open(envf, 'w', encoding='utf-8') as fh:
            fh.write(f"Python={sys.version.split()[0]}\n")
            fh.write(f"Platform={sys.platform}\n")
    except Exception:
        pass
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook para adjuntar información a Allure cuando un test falla.

    - Adjunta screenshot si el test usa la fixture `driver` (Selenium).
    - Adjunta el longrepr/texto del fallo.
    """
    outcome = yield
    rep = outcome.get_result()
    # Solo nos interesa la fase 'call' (ejecución del test)
    if rep.when != 'call':
        return

    if rep.failed:
        try:
            # Si el test proporciona un WebDriver, adjuntar screenshot
            if 'driver' in getattr(item, 'funcargs', {}):
                try:
                    driver = item.funcargs['driver']
                    png = None
                    try:
                        png = driver.get_screenshot_as_png()
                    except Exception:
                        # algunos drivers/devices pueden no soportar screenshots
                        png = None
                    if png:
                        try:
                            allure.attach(png, name='screenshot', attachment_type=allure.attachment_type.PNG)
                        except Exception:
                            pass
                except Exception:
                    pass

            # Adjuntar la representación larga del fallo (stacktrace/text)
            longrepr = getattr(rep, 'longrepr', None)
            text = None
            try:
                # rep.longrepr puede ser un objeto complejo; convertir a str es seguro
                text = str(longrepr)
            except Exception:
                text = None
            if text:
                try:
                    allure.attach(text, name='failure', attachment_type=allure.attachment_type.TEXT)
                except Exception:
                    pass
        except Exception:
            # no dejar que el hook rompa la ejecución de pytest
            pass
