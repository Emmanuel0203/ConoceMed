class Localidad:
    def __init__(self, idLocalidad, nombre, numero, fkIdCiudad):
        self.id = idLocalidad
        self.nombre = nombre
        self.numero = numero
        self.fkIdCiudad = fkIdCiudad

    @classmethod
    def from_dict(cls, data):
        return cls(
            idLocalidad=data.get("idLocalidad"),
            nombre=data.get("nombre"),
            numero=data.get("numero"),
            fkIdCiudad=data.get("fkIdCiudad"),
        )
