from flask import Blueprint, render_template

# Definir blueprint
vistaInicio = Blueprint("vistaInicio", __name__, template_folder="../templates")

@vistaInicio.route("/inicio", methods=["GET"])
def home():
    """
    Página de inicio que carga el template base.html
    """
    return render_template("index.html")
