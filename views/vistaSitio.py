from flask import Blueprint, render_template
from controllers.controlSitio import obtener_sitios

vistaSitio = Blueprint("vistaSitio", __name__)

@vistaSitio.route("/sitios")
def listar_sitios():
    sitios = obtener_sitios()
    return render_template("sitios.html", sitios=sitios)
