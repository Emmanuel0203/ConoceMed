"""
Pruebas E2E (End-to-End) usando Selenium.

Este test levanta el servidor de pruebas de Flask (importando `main.app`),
arranca un navegador Chrome (mediante webdriver-manager) en modo headless
y solicita la ruta `/`. Comprueba que la respuesta contiene el texto
esperado. Documentación y mensajes en español.

Requisitos locales para ejecutar:
- Python packages: selenium, webdriver-manager
- Chrome o Chromium instalado en la máquina donde se ejecuta el test

Si falta Selenium o webdriver-manager, el test se marcará como "skipped".

Ejecutar localmente (PowerShell):
    .\env\Scripts\Activate.ps1
    pip install selenium webdriver-manager
    pytest tests/e2e -q

"""
from threading import Thread
import pytest

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:
    webdriver = None


@pytest.fixture(scope='session')
def server():
    """Levanta la app Flask en un servidor WSGI en puerto 5001 para pruebas E2E.

    Devuelve la URL base (p. ej. 'http://localhost:5001').
    """
    try:
        from main import app as main_app
    except Exception as e:
        pytest.skip(f"No se pudo importar main.app: {e}")

    # usar werkzeug make_server para controlar el ciclo de vida
    from werkzeug.serving import make_server

    srv = make_server('localhost', 5001, main_app)
    thread = Thread(target=srv.serve_forever)
    thread.daemon = True
    thread.start()
    yield 'http://localhost:5001'
    try:
        srv.shutdown()
        thread.join(timeout=5)
    except Exception:
        pass


@pytest.fixture(scope='session')
def driver():
    """Crea un WebDriver Chrome (headless) usando webdriver-manager.

    Si selenium/webdriver-manager no está instalado, skip.
    """
    if webdriver is None:
        pytest.skip('selenium o webdriver-manager no están instalados')

    options = webdriver.ChromeOptions()
    # Ejecutar headless para CI; puedes quitar si quieres ver el navegador
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=options)
    yield drv
    try:
        drv.quit()
    except Exception:
        pass


def test_home_e2e(driver, server):
    """Prueba E2E simple: la página raíz carga y contiene la marca 'index'."""
    url = server + '/'
    driver.get(url)
    assert 'index' in driver.page_source
