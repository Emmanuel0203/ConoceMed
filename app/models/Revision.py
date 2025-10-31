class Revision:
    def __init__(self, idRevision, decision, comentario, fecha, fkIdUsuario, fkIdLugar_Sugerido):
        self.id = idRevision
        self.decision = decision
        self.comentario = comentario
        self.fecha = fecha
        self.fkIdUsuario = fkIdUsuario
        self.fkIdLugar_Sugerido = fkIdLugar_Sugerido

    @classmethod
    def from_dict(cls, data):
        return cls(
            idRevision=data.get("idRevision"),
            decision=data.get("decision"),
            comentario=data.get("comentario"),
            fecha=data.get("fecha"),
            fkIdUsuario=data.get("fkIdUsuario"),
            fkIdLugar_Sugerido=data.get("fkIdLugar_Sugerido"),
        )
