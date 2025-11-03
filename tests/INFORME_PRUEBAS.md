# Informe de Pruebas — Proyecto ConoceMed

Fecha: 2025-11-01

1. Introducción

Este documento resume el trabajo de pruebas automatizadas aplicado al proyecto ConoceMed (módulo USB-ConoceMed). El objetivo fue crear pruebas unitarias/funcionales para las vistas principales, integrar pruebas E2E básicas con Selenium, emplear fixtures de pytest para setup/teardown, usar dobles de prueba (mocks) para dependencias externas y habilitar generación de reportes con Allure.

El foco estuvo en las vistas que exponen la funcionalidad principal: inicio, login, listado/detalle de sitios, sugeridos y administración (creación y uploads). Además se añadió un test E2E que arranca la app y comprueba la carga de la página raíz.

2. Herramienta de pruebas

Pytest: framework principal usado para tests. Complementos utilizados:

- `allure-pytest` (opcional) — para generar reportes interactivos.
- `webdriver-manager` + `selenium` — para el test E2E en `tests/e2e/test_e2e_selenium.py`.

a. Comando para crear el entorno virtual

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
pip install -r requirements.txt
```

b. Comando de ejecución para todas las pruebas

```powershell
python -m pytest -v
```

c. Comando para ejecutar y recolectar resultados para Allure

```powershell
pytest --alluredir=allure-results
# generar y ver reporte (requiere allure commandline)
allure serve allure-results
```

3. Tabla resumen

| Prueba | Tipo | ¿Qué verifica? |
|---|---:|---|
| `tests/views/test_vistaInicio.py::test_home_get` | Integración (Web) | GET a la ruta de inicio responde 200 y renderiza la plantilla. |
| `tests/views/test_vistaLogin.py::test_get_login` | Integración (Web) | GET a /login carga el formulario de login. |
| `tests/views/test_vistaLogin.py::test_post_login_success` | Integración (Web) | POST login con credenciales relevantes redirige/valida flujo de autenticación (mocked). |
| `tests/views/test_vistaSitio.py::test_listar_sitios` | Integración (Web) | Listado de sitios usa `APIClient` mockeado y devuelve datos esperados. |
| `tests/views/test_vistaSugerido.py::test_get_sugerir` | Integración (Web) | GET formulario de sugeridos carga correctamente. |
| `tests/views/test_vistaSugerido.py::test_get_lugares_json` | Integración (API) | GET a `/lugares.json` (o endpoint JSON) devuelve listado de localidades en JSON. |
| `tests/views/test_vistaSugerido.py::test_post_sugerir_success` | Integración (I/O) | POST multipart con archivo crea sugerido usando `APIClient` mock (simula upload). |
| `tests/views/test_vistaAdmin.py::test_admin_panel_get` | Integración (Web) | GET panel admin carga correctamente. |
| `tests/views/test_vistaAdmin.py::test_crear_lugar_post_with_file` | Integración (I/O) | POST crear lugar con archivo procesa upload y retorna éxito (mocked). |
| `tests/e2e/test_e2e_selenium.py::test_home_e2e` | E2E (Selenium) | Arranca servidor WSGI temporal y abre `/` en Chrome headless; comprueba que la página contiene la marca `index`. |

-- Unitarios / Funcionales ligeros --
| `tests/utils/test_api_client.py::test_get_data_handles_missing_env` | Unitario | Verifica que `APIClient` lanza ValueError si no está configurada la variable `API_URL`. |
| `tests/utils/test_api_client.py::test_make_request_get_ok` | Unitario / Integración | Mockea `requests.get` y verifica que `_make_request` / `get_data` devuelve JSON parseado cuando responde 200. |
| `tests/forms/test_formSugerido.py::test_form_sugerido_valida_en_contexto_de_app` | Unitario (Form) | Valida que `LugarSugeridoForm` pasa la validación en contexto de request con choices provistos. |
| `tests/controllers/test_controlSitio.py::test_obtener_sitios_mock` | Unitario | Mockea petición HTTP en `controlSitio` y verifica que devuelve una lista. |
| `tests/controllers/test_controlSitio.py::test_crear_sitio_permiso` | Unitario (Seguridad) | Comprueba que `crear_sitio` lanza PermissionError cuando el rol no es admin. |

-- Vistas básicas / Rutas estáticas --
| `tests/views/test_views_basic.py::test_index_se_muestra_correctamente` | Integración (Web) | Comprueba que la ruta raíz/index responde 200 y muestra contenido esperado. |
| `tests/views/test_views_basic.py::test_gastronomia_ruta_ok` | Integración (Web) | Comprueba que la ruta de gastronomía carga correctamente (status 200). |

-- End of table --

4. Detalle de Casos de Prueba

Todos los tests siguen la estructura: precondiciones, acción, resultado esperado y postcondiciones. A continuación se describen los principales casos (ejemplos representativos).

Test Case 4.1 – Inicio (GET `/`)
Preconditions:

- La app Flask (`main.app`) es importable.
- `APIClient` está mockeado por la fixture `mock_api` en `conftest.py`.

Action: `client.get('/')`

Expected Response: HTTP 200 y contenido que incluye el marcador 'index'.

Success/Fail: ✔ / ✖

Postcondition: Ningún recurso persistente creado.

Test Case 4.2 – Login POST (flujo autenticación)
Preconditions:

- Formulario de login disponible; `autenticar_usuario` y `login_user` se mockean en pruebas unitarias si hace falta.

Action: `client.post('/login', data={...})`

Expected Response: Redirección o status esperado para login exitoso. ✔

Postcondition: No se mantiene sesión real fuera del contexto de la prueba.

Test Case 4.3 – Crear sugerido con upload (multipart)
Preconditions:

- `tmp_upload_dir` fixture proporciona carpeta temporal.
- `APIClient.insert_data` está mockeado para devolver éxito.

Action: `client.post('/sugerir', data=multipart_files_and_fields)`

Expected Response: 200/redirect y `APIClient.insert_data` llamado con archivos y datos apropiados. ✔

Postcondition: Archivos temporales escritos en `tmp_upload_dir` son limpiados al finalizar la prueba.

Test Case 4.4 – Admin crear lugar con archivo
Preconditions: `mock_api` y `tmp_upload_dir` disponibles.

Action: `client.post('/admin/crear', data=multipart)`

Expected Response: Confirmación de creación (success True en stub). ✔

Test Case 4.5 – E2E: carga de la página raíz con Selenium
Preconditions:

- `selenium` y `webdriver-manager` instalados localmente (o test marcado como skip si faltan).
- Chrome/Chromium instalado en la máquina.

Action: Arrancar servidor WSGI temporal en `localhost:5001` y usar WebDriver para `driver.get('http://localhost:5001/')`.

Expected Response: `driver.page_source` contiene la marca `index`. ✔

Postcondition: Driver cerrado; servidor detenido.

Test Case 4.6 – APIClient: falta de variable de entorno
Preconditions:

- El módulo `utils.api_client.APIClient` está disponible.

Action: Instanciar `APIClient('Usuario')` con `API_URL` vacío.

Expected Response: `ValueError` lanzado indicando configuración inválida. ✔

Postcondition: Ningún recurso persistente creado.

Test Case 4.7 – APIClient: respuesta 200 parseada
Preconditions:

- `requests.get` es parcheado para devolver un objeto con `status_code=200` y `json()` válido.

Action: Llamar `APIClient('Usuario').get_data()`.

Expected Response: Devuelve una lista (JSON parseado) sin lanzar excepciones. ✔

Postcondition: No hay llamadas reales a la red.

Test Case 4.8 – Validación de formulario LugarSugeridoForm
Preconditions:

- Contexto de request creado con `app.test_request_context`.
- `idLocalidad.choices` e `idCategoria_Turistica.choices` proporcionados en el test.

Action: Construir `LugarSugeridoForm` con datos mínimos y ejecutar `form.validate()`.

Expected Response: `form.validate()` devuelve True. ✔

Postcondition: No se crean recursos persistentes.

Test Case 4.9 – controlSitio: obtener lista y permisos
Preconditions:

- `controllers.controlSitio` importado.

Action 1: Parchear la petición HTTP y llamar `obtener_sitios()`.
Expected Response 1: Devuelve lista vacía o lista de dicts. ✔

Action 2: Llamar `crear_sitio({}, rol='user')`.
Expected Response 2: Lanza `PermissionError`. ✔

Postcondition: No hay efectos secundarios.

Test Case 4.10 – Obtener lugares en formato JSON (vista Sugerido)
Preconditions:

- La vista que sirve `/lugares.json` (o similar) está implementada y `APIClient` está mockeado.

Action: `client.get('/lugares.json')` (o la ruta usada en el proyecto).

Expected Response: HTTP 200 y JSON con la clave/estructura esperada (por ejemplo `datos` o lista de localidades). ✔

Postcondition: No hay llamadas reales a la red (mocked via `mock_api`).

5. Estrategias y buenas prácticas aplicadas

1) Separación de responsabilidades
- Se mantuvieron las vistas ligeras y se mockearon llamadas a `APIClient` para aislar la lógica web de las dependencias externas.

2) Fixtures reutilizables
- `tests/conftest.py` centraliza `app`, `client`, `tmp_upload_dir`, `mock_api` y utilidades de Allure.
- `tmp_upload_dir` evita escritura en el árbol del proyecto y asegura limpieza.

3) Dobles de prueba (monkeypatch)
- `APIClient` se reemplaza por `DummyAPI` en todas las pruebas para evitar llamadas de red.

4) Minimizar tests E2E
- Solo un test E2E se incluyó (flujo de carga de página). La mayoría de la cobertura se logró con tests de integración rápidos usando Flask `test_client`.

5) Integración con Allure
- `conftest.py` añade hooks para adjuntar screenshots y traces en fallos y genera `allure-results/environment.properties`.

6) Manejo de templates en tests
- Se usó `jinja2.DictLoader` en la fixture `app` para proporcionar plantillas mínimas y evitar errores 500 por templates ausentes.

6. Fallos encontrados y soluciones implementadas

- Error 500 por plantillas faltantes: solucionado inyectando plantillas mínimas con `DictLoader`.
- RuntimeError/CSRF por `secret_key` ausente: se fijó `app.secret_key` en la fixture de pruebas.
- Dependencia de Flask-Login (`current_user`): se inyectó `current_user` como `SimpleNamespace(is_authenticated=False)` en `context_processor`.
- Registro de `context_processor` después de la primera request: se añadió protección y fallback a `jinja_env.globals` en `conftest.py`.

7. Conclusión

La estrategia combinó tests de integración rápidos y un test E2E puntual para validar la integración completa. Se priorizó la estabilidad (fixtures y mocks) y la reproducibilidad (requirements gestionados). La integración con Allure permite obtener reportes ricos con screenshots y traces para debugging cuando hay fallos.

8. Informe de Allure generado

Resultados de Allure (si se generaron) se encuentran en la carpeta `allure-results/`. Para generar y visualizar el informe:

```powershell
pytest --alluredir=allure-results
allure serve allure-results
```

Si `allure` (commandline) no está disponible, puedes generar el reporte en CI o instalarlo localmente: https://docs.qameta.io/allure/

---

Archivo generado automáticamente basado en los tests existentes en `tests/`.
