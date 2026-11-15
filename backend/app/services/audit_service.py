
from datetime import datetime, timezone

from app.config.database import database


async def registrar_auditoria(
    *,
    usuario: dict,
    sello_id: str,
    postulacion_id: str,
    recurso: str,
    recurso_id: str,
    accion: str,
    metodo: str | None = None,
    estado_anterior: str | None = None,
    estado_nuevo: str | None = None,
    fecha_evento: datetime | None = None,
) -> None:
    """
    Registra una acción interna en la colección auditorias.

    Permite registrar cambios de estado y decisiones finales.
    Cuando se invoca dentro de una sesión vinculada mediante
    session.bind(), la inserción participa en esa transacción.
    """


    auditoria = {
        "usuario_id": str(usuario["_id"]),
        "rol": usuario["role"],
        "sello_id": str(sello_id),
        "postulacion_id": str(postulacion_id),
        "recurso": recurso,
        "recurso_id": str(recurso_id),
        "accion": accion,
        "fecha": fecha_evento or datetime.now(timezone.utc),
    }

    if (estado_anterior is None) != (estado_nuevo is None):
        raise ValueError(
            "Los estados anterior y nuevo deben proporcionarse juntos."
        )
    
    if metodo is not None:
        auditoria["metodo"] = metodo

    if estado_anterior is not None:
        auditoria["estado_anterior"] = estado_anterior

    if estado_nuevo is not None:
        auditoria["estado_nuevo"] = estado_nuevo

    await database.auditorias.insert_one(auditoria)
