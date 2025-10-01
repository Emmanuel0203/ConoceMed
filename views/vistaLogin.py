from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user
from controllers.controlLogin import autenticar_usuario
from forms.formLogin import LoginForm
from dotenv import load_dotenv
import os

load_dotenv()

vistaLogin = Blueprint('vistaLogin', __name__, template_folder='../templates')

@vistaLogin.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        correo = form.correo.data
        password = form.password.data

        exito, user = autenticar_usuario(correo, password)

        if exito and user:
            login_user(user)  # 👈 Aquí se guarda la sesión
            flash(f"Bienvenido, {user.nombre}", "success")
            return redirect(url_for("vistaAutenticacion.index"))
        else:
            flash("Correo o contraseña incorrectos", "danger")

    return render_template("login.html", form=form)
