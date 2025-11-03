import allure
from forms.formSugerido import LugarSugeridoForm


def test_form_sugerido_valida_en_contexto_de_app(app):
    """Prueba funcional: el formulario LugarSugeridoForm valida correctamente con datos mínimos."""
    with app.test_request_context('/', method='POST'):
        form = LugarSugeridoForm(data={
            'nombre': 'Lugar prueba',
            'direccion': 'Cll 1 #2-3',
            'descripcion': 'Descripción corta',
            'idLocalidad': '1',
            'idCategoria_Turistica': '1'
        })
        # El formulario contiene SelectField cuya lista de choices normalmente
        # se rellena desde las vistas. En el contexto de test debemos
        # proporcionar choices para que la validación funcione.
        form.idLocalidad.choices = [("1", "Localidad prueba")]
        form.idCategoria_Turistica.choices = [("1", "Categoría prueba")]

        # Validación debe pasar (campos requeridos presentes)
        assert form.validate() is True
