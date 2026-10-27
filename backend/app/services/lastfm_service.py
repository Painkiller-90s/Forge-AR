
from datetime import datetime, timezone

import httpx

from app.config.settings import settings


LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"


async def consultar_artista_lastfm(nombre_artista: str) -> dict:
    """Consulta estadísticas públicas de un artista en Last.fm."""

    nombre_artista = nombre_artista.strip()

    if not nombre_artista:
        raise ValueError("El nombre del artista es obligatorio.")

    if not settings.lastfm_api_key:
        raise RuntimeError("La API Key de Last.fm no está configurada.")

    params = {
        "method": "artist.getinfo",
        "artist": nombre_artista,
        "api_key": settings.lastfm_api_key,
        "format": "json",
        "autocorrect": 0,
    }

    async with httpx.AsyncClient(
        timeout=15.0,
        headers={
            "User-Agent": (
                "ForgeAR/1.0 "
                "(https://github.com/Painkiller-90s/Forge-AR)"
            )
        },
    ) as client:
        respuesta = await client.get(LASTFM_URL, params=params)
        respuesta.raise_for_status()

    datos = respuesta.json()

    if "error" in datos:
        raise RuntimeError(
            f"Last.fm devolvió un error: {datos.get('message', 'Desconocido')}"
        )

    artista = datos.get("artist")

    if not artista:
        raise RuntimeError("Last.fm no devolvió información del artista.")

    # Evitar asociar automáticamente un nombre diferente.
    if artista.get("name", "").casefold() != nombre_artista.casefold():
        raise ValueError("La identidad del artista requiere verificación.")

    estadisticas = artista.get("stats", {})

    return {
        "nombre": artista["name"],
        "mbid": artista.get("mbid") or None,
        "url": artista.get("url"),
        "oyentes_acumulados": int(estadisticas["listeners"]),
        "reproducciones_acumuladas": int(estadisticas["playcount"]),
        "fuente": "Last.fm API",
        "fecha_obtencion": datetime.now(timezone.utc).isoformat(),
    }
