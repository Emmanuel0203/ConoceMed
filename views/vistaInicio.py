from flask import Blueprint, render_template, request
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

    # Obtener lugares sugeridos pendientes para sección admin con paginación
    api_lugares = APIClient("Sitios")
    lugares = api_lugares.get_data()
    lugares_pendientes = [l for l in lugares if l.get("estado") == "Pendiente"]

    pagina = int(request.args.get('pagina', 1))
    tarjetas_por_pagina = 6
    inicio = (pagina - 1) * tarjetas_por_pagina
    fin = inicio + tarjetas_por_pagina
    lugares_paginados = lugares_pendientes[inicio:fin]

    total_paginas = (len(lugares_pendientes) + tarjetas_por_pagina - 1) // tarjetas_por_pagina

    return render_template(
        "index.html",
        form=form,
        localidades=localidades,
        lugares=lugares_paginados,
        pagina=pagina,
        total_paginas=total_paginas,
    )
