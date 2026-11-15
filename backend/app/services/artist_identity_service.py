
import asyncio
import logging
import time

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx

from app.config.database import database

from app.config.musicbrainz import (
    MUSICBRAINZ_TIMEOUT_SECONDS,
    MUSICBRAINZ_MIN_REQUEST_INTERVAL_SECONDS,
    MUSICBRAINZ_RETRY_INITIAL_DELAY_SECONDS,
    MUSICBRAINZ_RETRY_MAX_DELAY_SECONDS,
    MUSICBRAINZ_RETRY_BACKOFF_MULTIPLIER,
)


logger = logging.getLogger(__name__)

MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/artist/"

USER_AGENT = (
    "ForgeAR/1.0 "
    "(https://github.com/Painkiller-90s/Forge-AR)"
)


# Control de frecuencia de peticiones dentro del proceso.
_musicbrainz_request_lock = asyncio.Lock()

_ultima_peticion_musicbrainz = None


# --------------------------------------------------
# CONTROL DE FRECUENCIA
# --------------------------------------------------

async def _solicitar_musicbrainz(
    cliente: httpx.AsyncClient,
    mbid: str,
) -> httpx.Response:

    global _ultima_peticion_musicbrainz

    async with _musicbrainz_request_lock:

        ahora = time.monotonic()

        if _ultima_peticion_musicbrainz is not None:

            transcurrido = (
                ahora - _ultima_peticion_musicbrainz
            )

            espera = (
                MUSICBRAINZ_MIN_REQUEST_INTERVAL_SECONDS
                - transcurrido
            )

            if espera > 0:
                await asyncio.sleep(espera)

        _ultima_peticion_musicbrainz = time.monotonic()

        respuesta = await cliente.get(
            f"{MUSICBRAINZ_URL}{mbid}",
            params={
                "inc": "url-rels",
                "fmt": "json",
            },
            headers={
                "User-Agent": USER_AGENT
            },
        )

        return respuesta


# --------------------------------------------------
# INTERPRETAR RETRY-AFTER
# --------------------------------------------------

def _obtener_retry_after(
    respuesta: httpx.Response,
) -> float | None:

    valor = respuesta.headers.get("Retry-After")

    if not valor:
        return None

    # Retry-After expresado en segundos.
    try:
        return max(0.0, float(valor))

    except (TypeError, ValueError):
        pass

    # Retry-After expresado como fecha HTTP.
    try:

        fecha = parsedate_to_datetime(valor)

        if fecha.tzinfo is None:
            fecha = fecha.replace(
                tzinfo=timezone.utc
            )

        return max(
            0.0,
            (
                fecha - datetime.now(timezone.utc)
            ).total_seconds(),
        )

    except (TypeError, ValueError, OverflowError):
        return None


# --------------------------------------------------
# ESPERA PROGRESIVA
# --------------------------------------------------

def _siguiente_espera(
    espera_actual: float,
) -> float:

    return min(
        espera_actual
        * MUSICBRAINZ_RETRY_BACKOFF_MULTIPLIER,

        MUSICBRAINZ_RETRY_MAX_DELAY_SECONDS,
    )


# --------------------------------------------------
# CONSULTA CON REINTENTOS INDEFINIDOS
# --------------------------------------------------

async def _consultar_datos_musicbrainz(
    cliente: httpx.AsyncClient,
    mbid: str,
) -> dict:

    intento = 0

    espera_actual = (
        MUSICBRAINZ_RETRY_INITIAL_DELAY_SECONDS
    )

    while True:

        intento += 1

        try:

            respuesta = await _solicitar_musicbrainz(
                cliente,
                mbid,
            )

        except httpx.RequestError as exc:

            logger.warning(
                "MusicBrainz: error de conexión. "
                "Intento %s. Error: %s. "
                "Nuevo intento en %.1f segundos.",
                intento,
                type(exc).__name__,
                espera_actual,
            )

            await asyncio.sleep(espera_actual)

            espera_actual = _siguiente_espera(
                espera_actual
            )

            continue

        estado = respuesta.status_code

        # HTTP 429: demasiadas peticiones.
        # Respetar Retry-After cuando esté disponible.
        if estado == 429:

            espera_servidor = _obtener_retry_after(
                respuesta
            )

            espera = (
                espera_servidor
                if espera_servidor is not None
                else espera_actual
            )

            logger.warning(
                "MusicBrainz: HTTP 429. "
                "Intento %s. "
                "Reintentando en %.1f segundos.",
                intento,
                espera,
            )

            await asyncio.sleep(espera)

            espera_actual = _siguiente_espera(
                espera_actual
            )

            continue

        # Errores temporales del servidor.
        # También se contempla HTTP 408.
        if estado == 408 or 500 <= estado < 600:

            espera_servidor = _obtener_retry_after(
                respuesta
            )

            espera = (
                espera_servidor
                if espera_servidor is not None
                else espera_actual
            )

            logger.warning(
                "MusicBrainz: HTTP %s. "
                "Intento %s. "
                "Reintentando en %.1f segundos.",
                estado,
                intento,
                espera,
            )

            await asyncio.sleep(espera)

            espera_actual = _siguiente_espera(
                espera_actual
            )

            continue

        # Los errores permanentes no se reintentan.
        respuesta.raise_for_status()

        # Comprobar que la respuesta contiene JSON válido.
        try:

            datos = respuesta.json()

        except ValueError:

            logger.warning(
                "MusicBrainz: respuesta JSON inválida. "
                "Intento %s. "
                "Reintentando en %.1f segundos.",
                intento,
                espera_actual,
            )

            await asyncio.sleep(espera_actual)

            espera_actual = _siguiente_espera(
                espera_actual
            )

            continue

        if not isinstance(datos, dict):

            logger.warning(
                "MusicBrainz: estructura JSON inesperada. "
                "Intento %s.",
                intento,
            )

            await asyncio.sleep(espera_actual)

            espera_actual = _siguiente_espera(
                espera_actual
            )

            continue

        logger.info(
            "MusicBrainz respondió correctamente "
            "en el intento %s.",
            intento,
        )

        return datos


# --------------------------------------------------
# VERIFICAR IDENTIDAD CON MUSICBRAINZ
# --------------------------------------------------

async def verificar_identidad_musicbrainz(
    mbid: str | None,
    spotify_id: str,
) -> bool:

    if not mbid or not spotify_id:
        return False

    async with httpx.AsyncClient(
        timeout=MUSICBRAINZ_TIMEOUT_SECONDS
    ) as cliente:

        datos = await _consultar_datos_musicbrainz(
            cliente,
            mbid,
        )

    relaciones = datos.get("relations", [])

    if not isinstance(relaciones, list):
        return False

    for relacion in relaciones:

        if not isinstance(relacion, dict):
            continue

        url = relacion.get("url") or {}

        if not isinstance(url, dict):
            continue

        recurso = url.get("resource", "")

        if not isinstance(recurso, str):
            continue

        enlace = urlparse(recurso)

        if enlace.hostname != "open.spotify.com":
            continue

        partes = enlace.path.strip("/").split("/")

        if partes == ["artist", spotify_id]:
            return True

    return False


# --------------------------------------------------
# VERIFICAR IDENTIDAD UTILIZANDO CACHÉ
# --------------------------------------------------

async def verificar_identidad_con_cache(
    mbid: str | None,
    spotify_id: str,
) -> bool:

    if not mbid or not spotify_id:
        return False

    # Buscar una correspondencia previamente verificada.
    identidad = await database.identidades_artistas.find_one({
        "_id": spotify_id,
        "musicbrainz_mbid": mbid,
        "identidad_confirmada": True,
    })

    if identidad:
        return True

    # Consultar MusicBrainz.
    confirmada = await verificar_identidad_musicbrainz(
        mbid,
        spotify_id,
    )

    if not confirmada:
        return False

    # Guardar únicamente identidades verificadas.
    await database.identidades_artistas.update_one(
        {"_id": spotify_id},
        {
            "$set": {
                "musicbrainz_mbid": mbid,
                "identidad_confirmada": True,
                "fuente_verificacion": "MusicBrainz",
                "fecha_verificacion": datetime.now(
                    timezone.utc
                ),
            }
        },
        upsert=True,
    )

    return True
