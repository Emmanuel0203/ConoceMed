import os
from dotenv import load_dotenv
import requests
from flask import Blueprint, render_template, redirect, url_for, flash, Flask, request
import urllib.parse
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms.formLogin import LoginForm
from forms.formSugerido import LugarSugeridoForm
from models.Usuario import Usuario
from config import Config
from utils.api_client import APIClient
import logging

# Importar y registrar las rutas (endpoints) 
from views.vistaInicio import vistaInicio  
from views.vistaSitio import vistaSitio
from views.vistaLogin import vistaLogin
from views.vistaSugerido import vistaSugerido
from views.vistaAdmin import vistaAdmin



load_dotenv()


# Base directory absoluta del proyecto (archivo main.py)
basedir = os.path.abspath(os.path.dirname(__file__))

# Definir carpeta de uploads absoluta y exponerla en app.config
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'media')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = "tu_clave_secreta"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helpers para plantillas: exponer urllib.parse y un util para extraer filename
# Exponer la función urlparse en los globals de Jinja (no el módulo)
app.jinja_env.globals['urlparse'] = urllib.parse.urlparse
def filename_from_path(p):
    try:
        return os.path.basename(p)
    except Exception:
        return ''
app.jinja_env.globals['filename_from_path'] = filename_from_path

# Configuración Flask-Login
login_manager = LoginManager()
login_manager.login_view = "vistaLogin.login"
login_manager.init_app(app)

# Configurar el archivo de log
"""logging.basicConfig(
    filename='main.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)"""

@login_manager.user_loader
def load_user(user_id):
    # Recuperar datos del usuario desde la API
    api_client = APIClient("Usuario")
    user_data = api_client.get_data_by_id(user_id)
    if user_data:
        #print(f"[DEBUG] Usuario cargado: {user_data}")
        # Extraer el primer elemento de la lista "datos" antes de pasarlo a from_dict
        user_data = user_data.get("datos", [])[0] if user_data.get("datos") else None
        if user_data:
            user = Usuario.from_dict(user_data)
            return user
    #print("[DEBUG] Usuario no encontrado o datos inválidos.")
    return None

# Registrar blueprints
app.register_blueprint(vistaInicio, url_prefix="/inicio")
app.register_blueprint(vistaSitio, url_prefix="/sitios")
app.register_blueprint(vistaLogin, url_prefix="/login")
app.register_blueprint(vistaSugerido)
app.register_blueprint(vistaAdmin)


@app.route("/", methods=["GET", "POST"])
def index():
    form = LugarSugeridoForm()
    api_localidades = APIClient("Localidad")
    localidades_data = api_localidades.get_data()
    localidades = localidades_data.get("datos", []) if isinstance(localidades_data, dict) else localidades_data
    form.idLocalidad.choices = [(str(l["idLocalidad"]), l["nombre"]) for l in localidades]
    # Insertar opción vacía al inicio
    form.idLocalidad.choices.insert(0, ('', '-- Seleccione localidad --'))

    # Obtener categorías turísticas para selects o formularios
    api_categorias = APIClient("Categoria_Turistica")
    categorias_data = api_categorias.get_data()
    categorias = categorias_data.get("datos", []) if isinstance(categorias_data, dict) else categorias_data
    form.idCategoria_Turistica.choices = [(str(c["idCategoria_Turistica"]), c["nombre"]) for c in categorias]
    # Insertar opción vacía al inicio
    form.idCategoria_Turistica.choices.insert(0, ('', '-- Seleccione categoría --'))

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

    # Agregar debug para verificar datos enviados
    print("[DEBUG] Datos enviados al formulario:", form.data)


    return render_template(
        "index.html",
        form=form,
        localidades=localidades,
        categorias=categorias,
        lugares=lugares_paginados,
        pagina=pagina,
        total_paginas=total_paginas,
    )


@app.route("/gastronomia")
def gastronomia():
    return render_template("gastronomia.html")

@app.route("/hoteleria")
def hoteleria():
    return render_template("hoteleria.html")

@app.route("/patrimonio")
def patrimonio():
    return render_template("patrimonio_arte_cultura.html")


if __name__ == "__main__":
    app.run(debug=True)

    # Context processor para formularios y datos globales
@app.context_processor
def inject_global_forms():
    form = LugarSugeridoForm()
    api_localidades = APIClient("Localidad")
    localidades_data = api_localidades.get_data()
    localidades = localidades_data.get("datos", []) if isinstance(localidades_data, dict) else localidades_data
    form.idLocalidad.choices = [(str(l["idLocalidad"]), l["nombre"]) for l in localidades]
    # Insertar opción vacía al inicio
    form.idLocalidad.choices.insert(0, ('', '-- Seleccione localidad --'))

    api_categorias = APIClient("Categoria_Turistica")
    categorias_data = api_categorias.get_data()
    categorias = categorias_data.get("datos", []) if isinstance(categorias_data, dict) else categorias_data
    form.idCategoria_Turistica.choices = [(str(c["idCategoria_Turistica"]), c["nombre"]) for c in categorias]
    # Insertar opción vacía al inicio
    form.idCategoria_Turistica.choices.insert(0, ('', '-- Seleccione categoría --'))

    admin_token = app.config.get('ADMIN_UPLOADS_TOKEN')
    return dict(form=form, localidades=localidades, categorias=categorias, admin_uploads_token=admin_token)

@app.route("/ruta_ejemplo", methods=["GET", "POST"])
def ruta_ejemplo():
    form = LugarSugeridoForm()

    # Debug para verificar datos recibidos en la solicitud
    print("[DEBUG] Datos recibidos en request.form:", request.form)
    print("[DEBUG] Archivos recibidos en request.files:", request.files)

    # Validar el formulario
    if form.validate_on_submit():
        print("[DEBUG] Formulario válido")
        # Aquí va el código para manejar el formulario válido
    else:
        print("[DEBUG] Errores en el formulario:", form.errors)

    return render_template("pagina_ejemplo.html", form=form)
