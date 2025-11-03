class TipoMulti:
    def __init__(self, idTipo_Multi, nombre):
        self.id = idTipo_Multi
        self.nombre = nombre

    @classmethod
    def from_dict(cls, data):
        return cls(
            idTipo_Multi=data.get("idTipo_Multi"),
            nombre=data.get("nombre"),
        )
