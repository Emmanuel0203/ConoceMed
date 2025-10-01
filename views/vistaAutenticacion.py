from flask import Blueprint, render_template
from flask_login import login_required, current_user
from dotenv import load_dotenv
import os

load_dotenv() 

vistaAutenticacion = Blueprint('vistaAutenticacion', __name__, template_folder='../templates')

@vistaAutenticacion.route("/")
@login_required
def index():
    return render_template("index.html", user=current_user)
