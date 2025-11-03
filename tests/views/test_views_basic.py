import allure


def test_index_se_muestra_correctamente(client):
    """Prueba funcional: la página de inicio carga correctamente y devuelve 200."""
    with allure.step("Solicitar la ruta / y comprobar el código de estado"):
        resp = client.get("/")
        assert resp.status_code == 200


@allure.feature("Vistas")
@allure.story("Página gastronomía")
def test_gastronomia_ruta_ok(client):
    """Prueba básica: la ruta /gastronomia devuelve 200 y renderiza la plantilla."""
    resp = client.get("/gastronomia")
    assert resp.status_code == 200
