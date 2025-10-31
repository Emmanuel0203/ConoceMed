class Rol:
    def __init__(self, idRol, nombre=None):
        self.id = idRol
        self.nombre = nombre

    @classmethod
    def from_dict(cls, data):
        return cls(
            idRol=data.get("idRol"),
            nombre=data.get("nombre")
        )