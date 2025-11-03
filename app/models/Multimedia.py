class Multimedia:
    def __init__(self, idMultimedia, titulo, url, descripcion, fkIdTipo_Multi):
        self.id = idMultimedia
        self.titulo = titulo
        self.url = url
        self.descripcion = descripcion
        self.fkIdTipo_Multi = fkIdTipo_Multi

    @classmethod
    def from_dict(cls, data):
        return cls(
            idMultimedia=data.get("idMultimedia"),
            titulo=data.get("titulo"),
            url=data.get("url"),
            descripcion=data.get("descripcion"),
            fkIdTipo_Multi=data.get("fkIdTipo_Multi"),
        )

