class Departamento:
    def __init__(self, idDepartamento, nombre, fkIdPais):
        self.id = idDepartamento
        self.nombre = nombre
        self.fkIdPais = fkIdPais

    @classmethod
    def from_dict(cls, data):
        return cls(
            idDepartamento=data.get("idDepartamento"),
            nombre=data.get("nombre"),
            fkIdPais=data.get("fkIdPais"),
        )

