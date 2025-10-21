from flask_login import UserMixin

class Usuario(UserMixin):
    def __init__(self, idusuario, nombre, apellido, correo, telefono, fkidrol, password):
        self.id = idusuario  # Flask-Login usa `id`
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.telefono = telefono
        self.fkidrol = fkidrol
        self.password = password

    @classmethod
    def from_dict(cls, data):
        return cls(
            idusuario=data.get("idUsuario"),  # Corregido para usar "idUsuario" en lugar de "idusuario"
            nombre=data.get("nombre"),
            apellido=data.get("apellido"),
            correo=data.get("correo"),
            telefono=data.get("telefono"),
            fkidrol=data.get("fkidRol"),
            password=data.get("password")
        )

    @property
    def is_admin(self):
        # Compara el fkidrol con el ID del rol de administrador
        is_admin = self.fkidrol == "1dd96a79-3a98-409d-b875-8585aca8315a"
        return is_admin
