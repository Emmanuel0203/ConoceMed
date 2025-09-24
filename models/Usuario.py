class Usuario:
    def __init__(self, idUsuario, nombre, apellido, correo, telefono, fkIdRol):
        self.id = idUsuario
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.telefono = telefono
        self.fkIdRol = fkIdRol

    @classmethod
    def from_dict(cls, data):
        return cls(
            idUsuario=data.get("idUsuario"),
            nombre=data.get("nombre"),
            apellido=data.get("apellido"),
            correo=data.get("correo"),
            telefono=data.get("telefono"),
            fkIdRol=data.get("fkIdRol"),
        )






















