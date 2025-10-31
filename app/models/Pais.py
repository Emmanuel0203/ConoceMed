class Pais:
    def __init__(self, idPais, nombre):
        self.id = idPais
        self.nombre = nombre


    @classmethod
    def from_dict(cls, data):
        """Convierte un diccionario (JSON de la API) en un objeto SitioTuristico"""
        return cls(
            idPais=data.get("idPais"),
            nombre=data.get("nombre"),
        )
