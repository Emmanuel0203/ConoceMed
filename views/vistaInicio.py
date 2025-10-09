from flask import Blueprint, render_template
from forms.formSugerido import LugarSugeridoForm
from utils.api_client import APIClient

# Definir blueprint
vistaInicio = Blueprint("vistaInicio", __name__, template_folder="../templates")

@vistaInicio.route("/inicio", methods=["GET"])
def home():
    """
    Página de inicio que carga el template base.html con contexto necesario
    """
    form = LugarSugeridoForm()
    api_localidades = APIClient("Localidad")
    localidades_data = api_localidades.get_data()
    localidades = localidades_data.get("datos", []) if isinstance(localidades_data, dict) else localidades_data
    form.idLocalidad.choices = [(str(l["idLocalidad"]), l["nombre"]) for l in localidades]
    return render_template("index.html", form=form, localidades=localidades)
