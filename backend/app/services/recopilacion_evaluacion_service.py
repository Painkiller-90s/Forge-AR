
import logging

from bson import ObjectId

from app.config.database import database

from app.services.spotify_service import (
    consultar_artista_spotify,
    consultar_catalogo_spotify,
    extraer_id_artista_spotify,
)

from app.services.instagram_service import (
    extraer_usuario_instagram,
    obtener_metricas_instagram,
)

from app.services.metricas_cache_service import (
    guardar_metricas_validas,
    recuperar_ultimas_metricas,
)

from app.services.lastfm_service import (
    ArtistaLastFMNoEncontrado,
    consultar_artista_lastfm,
)

from app.services.lastfm_cache_service import (
    obtener_metricas_lastfm_cache,
    guardar_metricas_lastfm_cache,
    recuperar_ultimas_metricas_lastfm_cache,
)

from app.services.artist_identity_service import (
    verificar_identidad_con_cache,
)


logger = logging.getLogger(__name__)


async def _obtener_spotify(
    postulacion_id: str,
    sello_id: str,
    spotify_url: str | None,
) -> tuple[dict | None, str | None]:

    if not spotify_url:
        return None, None

    try:
        spotify_id = extraer_id_artista_spotify(spotify_url)
    except ValueError:
        logger.warning(
            "HU009: Enlace de Spotify inválido para %s",
            postulacion_id,
        )
        return None, None

    try:
        perfil = await consultar_artista_spotify(spotify_id)
        catalogo = await consultar_catalogo_spotify(spotify_id)

        metricas = {
            "perfil": perfil,
            "catalogo": catalogo,
            "fuente": "Spotify Web API",
            "fecha_obtencion": perfil["fecha_obtencion"],
            "estado_metricas": "actualizadas",
        }

        try:
            await guardar_metricas_validas(
                postulacion_id=postulacion_id,
                sello_id=sello_id,
                plataforma="spotify",
                cuenta_id=spotify_id,
                metricas=metricas,
            )
        except Exception:
            logger.exception(
                "HU009: No fue posible guardar Spotify para %s",
                postulacion_id,
            )

        return metricas, spotify_id

    except Exception:
        logger.exception(
            "HU009: Falló la consulta de Spotify para %s",
            postulacion_id,
        )

    # Recuperar el último respaldo disponible.
    try:
        respaldo = await recuperar_ultimas_metricas(
            postulacion_id=postulacion_id,
            sello_id=sello_id,
            plataforma="spotify",
            cuenta_id=spotify_id,
        )

        if (
            isinstance(respaldo, dict)
            and isinstance(respaldo.get("perfil"), dict)
            and isinstance(respaldo.get("catalogo"), dict)
        ):
            return respaldo, spotify_id

    except Exception:
        logger.exception(
            "HU009: Falló el respaldo de Spotify para %s",
            postulacion_id,
        )

    return None, spotify_id


async def _obtener_instagram(
    postulacion_id: str,
    sello_id: str,
    instagram_url: str | None,
) -> dict | None:

    if not instagram_url:
        return None

    try:
        usuario = extraer_usuario_instagram(instagram_url)
    except ValueError:
        logger.warning(
            "HU009: Enlace de Instagram inválido para %s",
            postulacion_id,
        )
        return None

    try:
        metricas = await obtener_metricas_instagram(
            instagram_url
        )

        try:
            await guardar_metricas_validas(
                postulacion_id=postulacion_id,
                sello_id=sello_id,
                plataforma="instagram",
                cuenta_id=usuario,
                metricas=metricas,
            )
        except Exception:
            logger.exception(
                "HU009: No fue posible guardar Instagram para %s",
                postulacion_id,
            )

        return metricas

    except Exception:
        logger.exception(
            "HU009: Falló la consulta de Instagram para %s",
            postulacion_id,
        )

    # Recuperar el último respaldo disponible.
    try:
        respaldo = await recuperar_ultimas_metricas(
            postulacion_id=postulacion_id,
            sello_id=sello_id,
            plataforma="instagram",
            cuenta_id=usuario,
        )

        if isinstance(respaldo, dict):
            return respaldo

    except Exception:
        logger.exception(
            "HU009: Falló el respaldo de Instagram para %s",
            postulacion_id,
        )

    return None


async def _obtener_lastfm(
    postulacion_id: str,
    spotify_id: str | None,
    nombre_artista: str | None,
) -> tuple[dict | None, bool | None, bool]:

    if not spotify_id or not nombre_artista:
        return None, None, False

    lastfm = None
    perfil_encontrado = True
    consulta_nueva = False

    # 1. Consultar primero la caché vigente.
    try:
        lastfm = await obtener_metricas_lastfm_cache(
            spotify_id
        )
    except Exception:
        logger.exception(
            "HU009: Error consultando caché Last.fm para %s",
            postulacion_id,
        )

    if lastfm is not None:
        lastfm["estado_metricas"] = "actualizadas"

    else:
        # 2. Consultar Last.fm si no existe caché vigente.
        try:
            lastfm = await consultar_artista_lastfm(
                nombre_artista
            )
            consulta_nueva = True

        except ArtistaLastFMNoEncontrado:
            logger.info(
                "HU009: Artista no encontrado en Last.fm para %s",
                postulacion_id,
            )

            # No confundir un artista inexistente con
            # una interrupción temporal del proveedor.
            return None, False, False

        except Exception:
            logger.exception(
                "HU009: Falló Last.fm para %s",
                postulacion_id,
            )

            # 3. Recuperar métricas históricas.
            try:
                lastfm = (
                    await recuperar_ultimas_metricas_lastfm_cache(
                        spotify_id
                    )
                )
            except Exception:
                logger.exception(
                    "HU009: Falló el respaldo de Last.fm para %s",
                    postulacion_id,
                )

            if lastfm is None:
                return None, None, False

            lastfm["estado_metricas"] = "desactualizadas"

    # 4. Verificar identidad mediante MusicBrainz.
    identidad_confirmada = False

    try:
        identidad_confirmada = (
            await verificar_identidad_con_cache(
                lastfm.get("mbid"),
                spotify_id,
            )
        )

    except Exception:
        logger.exception(
            "HU009: No fue posible verificar MusicBrainz para %s",
            postulacion_id,
        )

    # 5. Guardar únicamente datos nuevos y verificados.
    if identidad_confirmada and consulta_nueva:
        try:
            await guardar_metricas_lastfm_cache(
                spotify_id=spotify_id,
                metricas=lastfm,
                identidad_confirmada=True,
            )
        except Exception:
            logger.exception(
                "HU009: No fue posible guardar Last.fm para %s",
                postulacion_id,
            )

    return lastfm, perfil_encontrado, identidad_confirmada


async def recopilar_metricas_evaluacion(
    postulacion_id: str,
    sello_id: str,
) -> dict | None:
    """
    Coordina la recopilación automática de fuentes externas
    para la generación de un reporte HU009.

    Los errores individuales de los proveedores no detienen
    el proceso. Se intenta recuperar el último respaldo válido.
    """

    if not ObjectId.is_valid(postulacion_id):
        return None

    postulacion = await database.postulaciones.find_one({
        "_id": ObjectId(postulacion_id),
        "sello_id": sello_id,
    })

    if not postulacion:
        return None

    press_kit = postulacion.get("press_kit") or {}

    # 1. Spotify.
    spotify, spotify_id = await _obtener_spotify(
        postulacion_id,
        sello_id,
        press_kit.get("spotify_url"),
    )

    # 2. Instagram.
    instagram = await _obtener_instagram(
        postulacion_id,
        sello_id,
        press_kit.get("instagram_url"),
    )

    # 3. Last.fm y verificación MusicBrainz.
    nombre_artista = (
        spotify.get("perfil", {}).get("nombre")
        if spotify
        else None
    )

    lastfm, perfil_lastfm_encontrado, identidad_confirmada = (
        await _obtener_lastfm(
            postulacion_id,
            spotify_id,
            nombre_artista,
        )
    )

    return {
        "spotify": spotify,
        "instagram": instagram,
        "lastfm": lastfm,
        "perfil_lastfm_encontrado": perfil_lastfm_encontrado,
        "identidad_confirmada": identidad_confirmada,
    }
