from urllib.parse import urlparse
import httpx
from datetime import datetime, timezone
from app.config.database import database


MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/artist/"
USER_AGENT = (
    "ForgeAR/1.0 "
    "(https://github.com/Painkiller-90s/Forge-AR)"
)


async def verificar_identidad_musicbrainz(
    mbid: str | None,
    spotify_id: str,
) -> bool:
    """Verifica la relación entre MusicBrainz y Spotify."""

    if not mbid or not spotify_id:
        return False

    async with httpx.AsyncClient(timeout=15.0) as client:
        respuesta = await client.get(
            f"{MUSICBRAINZ_URL}{mbid}",
            params={
                "inc": "url-rels",
                "fmt": "json",
            },
            headers={"User-Agent": USER_AGENT},
        )

        respuesta.raise_for_status()

    datos = respuesta.json()

    for relacion in datos.get("relations", []):
        recurso = (relacion.get("url") or {}).get(
            "resource", ""
        )

        enlace = urlparse(recurso)

        if enlace.hostname != "open.spotify.com":
            continue

        partes = enlace.path.strip("/").split("/")

        if partes == ["artist", spotify_id]:
            return True

    return False


async def verificar_identidad_con_cache(
    mbid: str | None,
    spotify_id: str,
) -> bool:
    """
    Reutiliza una identidad previamente verificada o consulta
    MusicBrainz si todavía no existe una correspondencia válida.
    """

    if not mbid or not spotify_id:
        return False

    # Buscar una correspondencia ya verificada.
    identidad = await database.identidades_artistas.find_one({
        "_id": spotify_id,
        "musicbrainz_mbid": mbid,
        "identidad_confirmada": True,
    })

    if identidad:
        return True

    # Verificar la identidad mediante MusicBrainz.
    confirmada = await verificar_identidad_musicbrainz(
        mbid,
        spotify_id,
    )

    if not confirmada:
        return False

    # Guardar únicamente los identificadores verificados.
    await database.identidades_artistas.update_one(
        {"_id": spotify_id},
        {
            "$set": {
                "musicbrainz_mbid": mbid,
                "identidad_confirmada": True,
                "fuente_verificacion": "MusicBrainz",
                "fecha_verificacion": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    return True
