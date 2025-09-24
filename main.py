from flask import Blueprint, render_template, redirect, url_for, flash, Flask
from config import Config

# Importar y registrar las rutas (endpoints) 
from views.vistaUsuario import vistaUsuario
from views.vistaInicio import vistaInicio  
from views.vistaSitio import vistaSitio
from views.vistaLogin import vistaLogin


app = Flask(__name__)
app.config.from_object(Config)

# Registrar blueprints
app.register_blueprint(vistaUsuario, url_prefix="/usuarios")
app.register_blueprint(vistaInicio, url_prefix="/inicio")
app.register_blueprint(vistaSitio, url_prefix="/sitios")
app.register_blueprint(vistaLogin, url_prefix='/login')


@app.route("/")
def index():
    return render_template("index.html")


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
