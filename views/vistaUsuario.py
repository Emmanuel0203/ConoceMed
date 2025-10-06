"""
Módulo de vistas para la gestión de usuarios en la API.

Contiene los endpoints expuestos a través de un Blueprint de Flask
que permiten realizar operaciones CRUD sobre los usuarios.

Endpoints disponibles:
- GET    /api/usuarios/            → Listar todos los usuarios
- GET    /api/usuarios/<id>        → Consultar un usuario por ID
- POST   /api/usuarios/            → Crear un nuevo usuario
- PUT    /api/usuarios/<id>        → Modificar un usuario existente
- DELETE /api/usuarios/<id>        → Eliminar un usuario
"""

from flask import Blueprint, jsonify, request
from controllers.controlUsuario import ControlUsuario

# Definición del Blueprint que agrupa las rutas de usuario
vistaUsuario = Blueprint("vistaUsuario", __name__)
control = ControlUsuario()


# ============================
# GET - Listar todos los usuarios
# ============================
@vistaUsuario.route("/", methods=["GET"])
def listar_usuarios():
    """
    Obtiene el listado completo de usuarios almacenados en la base de datos.

    Returns:
        JSON: Lista de usuarios en formato JSON con campos
              idUsuario, nombre y correo.
    """
    usuarios = control.listar()
    return jsonify([{"id": u.idUsuario, "nombre": u.nombre, "correo": u.correo} for u in usuarios])



# ============================
# GET - Consultar un usuario por ID
# ============================
@vistaUsuario.route("/<int:idUsuario>", methods=["GET"])
def consultar_usuario(idUsuario):
    """
    Consulta un usuario específico por su ID.

    Args:
        idUsuario (int): Identificador único del usuario.

    Returns:
        JSON: Datos del usuario si existe, o un mensaje de error.
    """
    usuario = control.buscar_por_id(idUsuario)
    if usuario:
        return jsonify(
            {"idUsuario": usuario.idUsuario, "nombre": usuario.nombre, "correo": usuario.correo}
        ), 200
    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================
# POST - Crear usuario
# ============================
@vistaUsuario.route("/", methods=["POST"])
def crear_usuario():
    """
    Crea un nuevo usuario en la base de datos.

    Expects:
        JSON con los campos:
        - nombre (str): Nombre del usuario.
        - correo (str): Correo electrónico del usuario.

    Returns:
        JSON: Mensaje de confirmación y el ID asignado al nuevo usuario.
    """
    data = request.get_json()
    nombre = data.get("nombre")
    correo = data.get("correo")

    nuevo = control.guardar(nombre, correo)
    return jsonify({"mensaje": "Usuario creado", "idUsuario": nuevo.idUsuario}), 201


# ============================
# PUT - Modificar usuario
# ============================
@vistaUsuario.route("/<int:idUsuario>", methods=["PUT"])
def modificar_usuario(idUsuario):
    """
    Modifica los datos de un usuario existente.

    Args:
        idUsuario (int): Identificador del usuario a modificar.

    Expects:
        JSON con los campos:
        - nombre (str): Nuevo nombre.
        - correo (str): Nuevo correo electrónico.

    Returns:
        JSON: Mensaje de éxito o error si no se encontró el usuario.
    """
    data = request.get_json()
    nombre = data.get("nombre")
    correo = data.get("correo")

    actualizado = control.modificar(idUsuario, nombre, correo)
    if actualizado:
        return jsonify({"mensaje": "Usuario actualizado"}), 200
    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================
# DELETE - Eliminar usuario
# ============================
@vistaUsuario.route("/<int:idUsuario>", methods=["DELETE"])
def eliminar_usuario(idUsuario):
    """
    Elimina un usuario de la base de datos.

    Args:
        idUsuario (int): Identificador del usuario a eliminar.

    Returns:
        JSON: Mensaje de confirmación si se eliminó,
              o un mensaje de error si no existe.
    """
    eliminado = control.borrar(idUsuario)
    if eliminado:
        return jsonify({"mensaje": "Usuario eliminado"}), 200
    return jsonify({"error": "Usuario no encontrado"}), 404
