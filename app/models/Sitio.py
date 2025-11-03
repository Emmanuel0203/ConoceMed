class SitioTuristico:
    def __init__(self, idSitio_Turistico, nombre, direccion, latitud, longitud, descripcion,
                 horario_cierre, horario_apertura, tarifa, fkidLocalidad, fkidCategoria_Turistica):
        self.id = idSitio_Turistico
        self.nombre = nombre
        self.direccion = direccion
        self.latitud = latitud
        self.longitud = longitud
        self.descripcion = descripcion
        self.horario_cierre = horario_cierre
        self.horario_apertura = horario_apertura
        self.tarifa = tarifa
        self.fkidLocalidad = fkidLocalidad
        self.fkidCategoria_Turistica = fkidCategoria_Turistica

    @classmethod
    def from_dict(cls, data):
        """Convierte un diccionario (JSON de la API) en un objeto SitioTuristico"""
        return cls(
            idSitio_Turistico=data.get("idSitio_Turistico"),
            nombre=data.get("nombre"),
            direccion=data.get("direccion"),
            latitud=data.get("latitud"),
            longitud=data.get("longitud"),
            descripcion=data.get("descripcion"),
            horario_cierre=data.get("horario_cierre"),
            horario_apertura=data.get("horario_apertura"),
            tarifa=data.get("tarifa"),
            fkidLocalidad=data.get("fkidLocalidad"),
            fkidCategoria_Turistica=data.get("fkidCategoria_Turistica"),
        )
