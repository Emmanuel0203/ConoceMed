class LugarSugerido:
    def __init__(self, idLugar_Sugerido, nombre, direccion, latitud, longitud, descripcion,
                 horario_cierre, horario_apertura, tarifa):
        self.id = idLugar_Sugerido
        self.nombre = nombre
        self.direccion = direccion
        self.latitud = latitud
        self.longitud = longitud
        self.descripcion = descripcion
        self.horario_cierre = horario_cierre
        self.horario_apertura = horario_apertura
        self.tarifa = tarifa

    @classmethod
    def from_dict(cls, data):
        return cls(
            idLugar_Sugerido=data.get("idLugar_Sugerido"),
            nombre=data.get("nombre"),
            direccion=data.get("direccion"),
            latitud=data.get("latitud"),
            longitud=data.get("longitud"),
            descripcion=data.get("descripcion"),
            horario_cierre=data.get("horario_cierre"),
            horario_apertura=data.get("horario_apertura"),
            tarifa=data.get("tarifa"),
        )

