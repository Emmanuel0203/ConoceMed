import os
from dotenv import load_dotenv
import requests
from flask import Blueprint, render_template, redirect, url_for, flash, Flask
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms.formLogin import LoginForm
from forms.formSugerido import LugarSugeridoForm
from models.Usuario import Usuario
from config import Config
from utils.api_client import APIClient

# Importar y registrar las rutas (endpoints) 
from views.vistaUsuario import vistaUsuario
from views.vistaInicio import vistaInicio  
from views.vistaSitio import vistaSitio
from views.vistaLogin import vistaLogin
from views.vistaSugerido import vistaSugerido



load_dotenv()


app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = "tu_clave_secreta"

# Configuración Flask-Login
login_manager = LoginManager()
login_manager.login_view = "vistaLogin.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # ⚠️ Aquí puedes reconsultar la API si quieres traer datos frescos del usuario
    return Usuario(user_id, None, None, None, None, None, None)

# Registrar blueprints
app.register_blueprint(vistaUsuario, url_prefix="/usuarios")
app.register_blueprint(vistaInicio, url_prefix="/inicio")
app.register_blueprint(vistaSitio, url_prefix="/sitios")
app.register_blueprint(vistaLogin, url_prefix="/login")
app.register_blueprint(vistaSugerido)


@app.route("/", methods=["GET", "POST"])
def index():
    form = LugarSugeridoForm()
    api_localidades = APIClient("Localidad")
    localidades_data = api_localidades.get_data()
    localidades = localidades_data.get("datos", []) if isinstance(localidades_data, dict) else localidades_data
    form.idLocalidad.choices = [(str(l["idLocalidad"]), l["nombre"]) for l in localidades]

    # ... otras inicializaciones/contexto ...

    return render_template(
        "index.html",
        form=form,
        localidades=localidades,
        # ...otros contextos necesarios...
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
