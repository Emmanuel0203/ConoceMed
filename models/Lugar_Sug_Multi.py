class LugarSugeridoMulti:
    def __init__(self, idLugarSugerido_Multi, fkIdLugar_Sugerido, fkIdMultimedia):
        self.id = idLugarSugerido_Multi
        self.fkIdLugar_Sugerido = fkIdLugar_Sugerido
        self.fkIdMultimedia = fkIdMultimedia

    @classmethod
    def from_dict(cls, data):
        return cls(
            idLugarSugerido_Multi=data.get("idLugarSugerido_Multi"),
            fkIdLugar_Sugerido=data.get("fkIdLugar_Sugerido"),
            fkIdMultimedia=data.get("fkIdMultimedia"),
        )

