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
            idusuario=data.get("idusuario"),
            nombre=data.get("nombre"),
            apellido=data.get("apellido"),
            correo=data.get("correo"),
            telefono=data.get("telefono"),
            fkidrol=data.get("fkidrol"),
            password=data.get("password")
        )
