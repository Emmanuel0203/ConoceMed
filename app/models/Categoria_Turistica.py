class CategoriaTuristica:
    def __init__(self, idCategoria_Turistica, nombre):
        self.id = idCategoria_Turistica
        self.nombre = nombre

    @classmethod
    def from_dict(cls, data):
        return cls(
            idCategoria_Turistica=data.get("idCategoria_Turistica"),
            nombre=data.get("nombre"),
        )