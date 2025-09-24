class SitioMulti:
    def __init__(self, idSitio_Multi, fkIdMultimedia, fkIdSitio_Turistico):
        self.id = idSitio_Multi
        self.fkIdMultimedia = fkIdMultimedia
        self.fkIdSitio_Turistico = fkIdSitio_Turistico

    @classmethod
    def from_dict(cls, data):
        return cls(
            idSitio_Multi=data.get("idSitio_Multi"),
            fkIdMultimedia=data.get("fkIdMultimedia"),
            fkIdSitio_Turistico=data.get("fkIdSitio_Turistico"),
        )