from flask import Blueprint, render_template, redirect, url_for, flash
from forms.formLugar_Sugerido import LugarSugeridoForm
import requests

vistaLugares = Blueprint("vistaLugares", __name__)
BASE_URL = "http://localhost:5031/api"  # tu API

@vistaLugares.route("/sugerir", methods=["GET", "POST"])
def sugerir_lugar():
    form = LugarSugeridoForm()
    if form.validate_on_submit():
        data = {
            "nombre": form.nombre.data,
            "direccion": form.direccion.data,
            "latitud": float(form.latitud.data),
            "longitud": float(form.longitud.data),
            "descripcion": form.descripcion.data,
            "estado": "Pendiente"
        }
        response = requests.post(f"{BASE_URL}/lugares_sugeridos", json=data)
        if response.status_code == 201:
            flash("¡Lugar sugerido con éxito!", "success")
            return redirect(url_for("vistaLugares.sugerir_lugar"))
        else:
            flash("Hubo un error al enviar la sugerencia", "danger")

    return render_template("sugerir_lugar.html", form=form)
