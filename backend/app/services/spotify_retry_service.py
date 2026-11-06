
import asyncio
import logging

import httpx


logger = logging.getLogger(__name__)

MAX_INTENTOS = 3
MAX_ESPERA_429 = 2.0


async def solicitar_spotify_con_reintentos(
    cliente: httpx.AsyncClient,
    metodo: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    """
    Realiza hasta tres intentos por solicitud HTTP.

    Reintenta errores de conexión, HTTP 5xx y HTTP 429
    cuando el tiempo de espera es aceptable.

    No reintenta errores permanentes como HTTP 400,
    401, 403 o 404.
    """

    for intento in range(1, MAX_INTENTOS + 1):
        try:
            respuesta = await cliente.request(
                metodo,
                url,
                **kwargs,
            )

        except httpx.RequestError as exc:
            logger.warning(
                "HU007: Error de conexión con Spotify. "
                "Intento %s/%s. Tipo: %s",
                intento,
                MAX_INTENTOS,
                type(exc).__name__,
            )

            if intento == MAX_INTENTOS:
                raise

            await asyncio.sleep(0.25 * (2 ** (intento - 1)))
            continue

        estado = respuesta.status_code

        if estado == 429:
            # Una cuota agotada no se soluciona con reintentos inmediatos.
            try:
                detalle = respuesta.json()
                razon = detalle.get("error", {}).get("reason")
            except (ValueError, AttributeError, TypeError):
                razon = None

            if razon == "QUOTA_EXCEEDED":
                logger.warning(
                    "HU007: Cuota de Spotify agotada."
                )
                return respuesta

            # Respetar Retry-After cuando se pueda esperar.
            try:
                espera = float(
                    respuesta.headers.get("Retry-After", "")
                )
            except (ValueError, TypeError):
                return respuesta

            if (
                intento == MAX_INTENTOS
                or espera < 0
                or espera > MAX_ESPERA_429
            ):
                return respuesta

            logger.warning(
                "HU007: Spotify devolvió HTTP 429. "
                "Intento %s/%s.",
                intento,
                MAX_INTENTOS,
            )

            await asyncio.sleep(espera)
            continue

        if 500 <= estado < 600 and intento < MAX_INTENTOS:
            logger.warning(
                "HU007: Spotify devolvió HTTP %s. "
                "Intento %s/%s.",
                estado,
                intento,
                MAX_INTENTOS,
            )

            await asyncio.sleep(0.25 * (2 ** (intento - 1)))
            continue

        return respuesta

    raise RuntimeError("Se agotaron los intentos de Spotify.")
