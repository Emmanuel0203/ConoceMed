from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
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
            try:
                # Guardar el id del usuario en session para que otras vistas lo usen
                session['user_id'] = getattr(user, 'id', None) or getattr(user, 'idusuario', None)
            except Exception:
                pass
            flash(f"Bienvenido, {user.nombre}", "success")
            return redirect(url_for("index"))
        else:
            flash("Correo o contraseña incorrectos", "danger")

    return render_template("login.html", form=form)


@vistaLogin.route("/logout")
@login_required
def logout():
    nombre = current_user.nombre  # solo para mostrar un mensaje amigable
    logout_user()  # 👈 Cierra la sesión
    # limpiar session
    try:
        session.pop('user_id', None)
    except Exception:
        pass
    flash(f"Hasta luego, {nombre}. Has cerrado sesión correctamente.", "info")
    return redirect(url_for("vistaInicio.home"))