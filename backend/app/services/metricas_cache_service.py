
from datetime import datetime, timezone

from app.config.database import database


async def guardar_metricas_validas(
    postulacion_id: str,
    sello_id: str,
    plataforma: str,
    cuenta_id: str,
    metricas: dict,
) -> None:
    """
    Conserva las últimas métricas válidas de una plataforma.

    No aplica vencimiento automático: los datos deben
    seguir disponibles si el proveedor externo falla.
    """

    if plataforma not in {"spotify", "instagram"}:
        raise ValueError("Plataforma no admitida.")

    if not cuenta_id:
        raise ValueError("La cuenta externa es obligatoria.")

    if not isinstance(metricas, dict) or not metricas:
        raise ValueError("Las métricas no son válidas.")

    fecha_obtencion = metricas.get("fecha_obtencion")

    if not fecha_obtencion:
        raise ValueError(
            "Las métricas deben incluir fecha de obtención."
        )

    await database.metricas_externas.update_one(
        {
            "postulacion_id": postulacion_id,
            "sello_id": sello_id,
            "plataforma": plataforma,
        },
        {
            "$set": {
                "cuenta_id": cuenta_id,
                "metricas": metricas,
                "fuente": metricas.get("fuente"),
                "fecha_obtencion": fecha_obtencion,
                "fecha_guardado": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )


async def recuperar_ultimas_metricas(
    postulacion_id: str,
    sello_id: str,
    plataforma: str,
    cuenta_id: str,
) -> dict | None:
    """
    Recupera las últimas métricas almacenadas.

    Solo devuelve datos de la misma postulación, sello,
    plataforma y cuenta externa.
    """

    registro = await database.metricas_externas.find_one({
        "postulacion_id": postulacion_id,
        "sello_id": sello_id,
        "plataforma": plataforma,
        "cuenta_id": cuenta_id,
    })

    if not registro:
        return None

    metricas = dict(registro["metricas"])
    metricas["estado_metricas"] = "desactualizadas"

    return metricas
