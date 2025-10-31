"""
Módulo de control de usuarios.

Contiene la lógica de negocio y las operaciones CRUD sobre la entidad Usuario.
Se comunica directamente con la base de datos a través de SQLAlchemy.
"""

from extensiones import db
from app.models.Usuario import Usuario


class ControlUsuario:
    """
    Clase encargada de manejar la lógica de negocio de los usuarios.
    Permite listar, crear, buscar, modificar y eliminar registros en la tabla Usuario.
    """

    def listar(self):
        """
        Obtiene todos los usuarios registrados.

        Returns:
            list[Usuario]: Lista de objetos Usuario.
        """
        return Usuario.query.all()

    def guardar(self, nombre, correo):
        """
        Guarda un nuevo usuario en la base de datos.

        Args:
            nombre (str): Nombre del usuario.
            correo (str): Correo electrónico del usuario.

        Returns:
            Usuario: El objeto usuario recién creado (con ID asignado).
        """
        usuario = Usuario(nombre=nombre, correo=correo)
        db.session.add(usuario)
        db.session.commit()
        return usuario

    def buscar_por_id(self, idUsuario):
        """
        Busca un usuario por su identificador.

        Args:
            idUsuario (int): Identificador único del usuario.

        Returns:
            Usuario | None: El usuario si existe, o None si no se encuentra.
        """
        return Usuario.query.get(idUsuario)

    def modificar(self, idUsuario, nombre, correo):
        """
        Modifica los datos de un usuario existente.

        Args:
            idUsuario (int): Identificador del usuario.
            nombre (str): Nuevo nombre.
            correo (str): Nuevo correo electrónico.

        Returns:
            Usuario | None: El usuario actualizado si existe, o None si no se encuentra.
        """
        usuario = Usuario.query.get(idUsuario)
        if usuario:
            usuario.nombre = nombre
            usuario.correo = correo
            db.session.commit()
            return usuario
        return None

    def borrar(self, idUsuario):
        """
        Elimina un usuario de la base de datos.

        Args:
            idUsuario (int): Identificador del usuario a eliminar.

        Returns:
            bool: True si el usuario fue eliminado, False si no se encontró.
        """
        usuario = Usuario.query.get(idUsuario)
        if usuario:
            db.session.delete(usuario)
            db.session.commit()
            return True
        return False
