
from datetime import datetime, timedelta, timezone

from app.config.database import database


# Vigencia inicial configurable por decisión del proyecto.
# No corresponde a una duración exigida por Last.fm.
VIGENCIA_CACHE_MINUTOS = 1440


async def obtener_metricas_lastfm_cache(
    spotify_id: str,
) -> dict | None:
    """Recupera las estadísticas si la caché está vigente."""

    ahora = datetime.now(timezone.utc)

    registro = await database.lastfm_cache.find_one({
        "_id": spotify_id,
        "vigente_hasta": {"$gt": ahora},
    })

    if not registro:
        return None

    campos = (
        "nombre",
        "mbid",
        "url",
        "oyentes_acumulados",
        "reproducciones_acumuladas",
        "fuente",
        "fecha_obtencion",
    )

    return {
        campo: registro[campo]
        for campo in campos
        if campo in registro
    }


async def guardar_metricas_lastfm_cache(
    spotify_id: str,
    metricas: dict,
    identidad_confirmada: bool,
) -> None:
    """Guarda temporalmente métricas de un artista verificado."""

    if not identidad_confirmada:
        return

    ahora = datetime.now(timezone.utc)

    await database.lastfm_cache.update_one(
        {"_id": spotify_id},
        {
            "$set": {
                "nombre": metricas["nombre"],
                "mbid": metricas["mbid"],
                "url": metricas["url"],
                "oyentes_acumulados": metricas["oyentes_acumulados"],
                "reproducciones_acumuladas": metricas[
                    "reproducciones_acumuladas"
                ],
                "fuente": metricas["fuente"],
                "fecha_obtencion": metricas["fecha_obtencion"],
                "fecha_guardado": ahora,
                "vigente_hasta": ahora + timedelta(
                    minutes=VIGENCIA_CACHE_MINUTOS
                ),
            }
        },
        upsert=True,
    )
