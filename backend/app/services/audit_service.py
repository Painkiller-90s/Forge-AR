
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
) -> None:
    """
    Registra una acción interna en la colección auditorias.

    La ruta que invoca este servicio debe haber validado
    previamente la identidad y los permisos del usuario.
    """

    auditoria = {
        "usuario_id": str(usuario["_id"]),
        "rol": usuario["role"],
        "sello_id": str(sello_id),
        "postulacion_id": str(postulacion_id),
        "recurso": recurso,
        "recurso_id": str(recurso_id),
        "accion": accion,
        "fecha": datetime.now(timezone.utc),
    }

    # Incluir información adicional cuando corresponda.
    if metodo is not None:
        auditoria["metodo"] = metodo

    # Guardar el evento en MongoDB.
    # Si falla, la excepción se comunica a la ruta que lo invocó.
    await database.auditorias.insert_one(auditoria)
