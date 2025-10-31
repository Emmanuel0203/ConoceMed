class Ciudad:
    def __init__(self, idCiudad, nombre, fkIdDepartamento):
        self.id = idCiudad
        self.nombre = nombre
        self.fkIdDepartamento = fkIdDepartamento

    @classmethod
    def from_dict(cls, data):
        return cls(
            idCiudad=data.get("idCiudad"),
            nombre=data.get("nombre"),
            fkIdDepartamento=data.get("fkIdDepartamento"),
        )
