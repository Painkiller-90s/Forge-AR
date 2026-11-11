
import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.config.database import database
from app.routes.auth_route import get_current_user

from app.services.spotify_service import (
    consultar_artista_spotify,
    extraer_id_artista_spotify,
)

from app.services.lastfm_service import (
    ArtistaLastFMNoEncontrado,
    consultar_artista_lastfm,
)

from app.services.lastfm_cache_service import (
    obtener_metricas_lastfm_cache,
    guardar_metricas_lastfm_cache,
)

from app.services.artist_identity_service import (
    verificar_identidad_con_cache,
)

from app.services.viability_service import (
    calcular_q_streaming,
)


router = APIRouter(prefix="/postulaciones", tags=["Last.fm"])
logger = logging.getLogger(__name__)


@router.get("/{postulacion_id}/lastfm")
async def consultar_lastfm_postulacion(
    postulacion_id: str,
    current_user: dict = Depends(get_current_user),
):
    # Solo evaluadores A&R autorizados.
    if current_user.get("role") != "ar":
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para consultar Last.fm.",
        )

    sello_id = current_user.get("label_id")

    if not sello_id:
        raise HTTPException(
            status_code=403,
            detail="El usuario no tiene un sello asignado.",
        )

    if not ObjectId.is_valid(postulacion_id):
        raise HTTPException(
            status_code=400,
            detail="ID de postulación inválido.",
        )

    # Consultar únicamente postulaciones del sello autorizado.
    postulacion = await database.postulaciones.find_one({
        "_id": ObjectId(postulacion_id),
        "sello_id": sello_id,
    })

    if not postulacion:
        raise HTTPException(
            status_code=404,
            detail="Postulación no encontrada.",
        )

    press_kit = postulacion.get("press_kit") or {}
    spotify_url = press_kit.get("spotify_url")

    if not spotify_url:
        raise HTTPException(
            status_code=422,
            detail="La postulación no tiene un enlace de Spotify.",
        )

    # Extraer identificador del artista de Spotify.
    try:
        spotify_id = extraer_id_artista_spotify(spotify_url)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="El enlace de Spotify no es válido.",
        ) from exc

    # Obtener información de Spotify y estadísticas de Last.fm.
    try:
        spotify = await consultar_artista_spotify(spotify_id)

        # Consultar primero la caché de MongoDB.
        lastfm = await obtener_metricas_lastfm_cache(spotify_id)

        cache_encontrada = lastfm is not None
        perfil_encontrado = True

        # Si no hay caché vigente, consultar Last.fm.
        if not cache_encontrada:
            try:
                lastfm = await consultar_artista_lastfm(
                    spotify["nombre"]
                )

            except ArtistaLastFMNoEncontrado:
                logger.info(
                    "HU008: Artista no encontrado en Last.fm para %s",
                    postulacion_id,
                )

                lastfm = None
                perfil_encontrado = False

    except Exception as exc:
        logger.exception(
            "HU008: Error al consultar métricas para %s",
            postulacion_id,
        )

        raise HTTPException(
            status_code=502,
            detail="No fue posible consultar las métricas externas.",
        ) from exc

    # Verificar identidad solamente cuando existe un perfil.
    identidad_confirmada = False

    if perfil_encontrado:
        try:
            identidad_confirmada = (
                await verificar_identidad_con_cache(
                    lastfm.get("mbid"),
                    spotify_id,
                )
            )

            estado = (
                "verificada"
                if identidad_confirmada
                else "pendiente_verificacion"
            )

        except Exception:
            logger.exception(
                "HU008: No fue posible verificar la identidad "
                "del artista para la postulación %s",
                postulacion_id,
            )

            identidad_confirmada = False
            estado = "verificacion_no_disponible"

    else:
        estado = "perfil_no_encontrado"

    # Guardar estadísticas nuevas únicamente si la identidad
    # fue confirmada.
    if identidad_confirmada and not cache_encontrada:
        try:
            await guardar_metricas_lastfm_cache(
                spotify_id,
                lastfm,
                identidad_confirmada,
            )

        except Exception:
            logger.exception(
                "HU008: No fue posible guardar la caché de Last.fm "
                "para la postulación %s",
                postulacion_id,
            )

    # Calcular Q_streaming utilizando la rúbrica de viabilidad.
    q_streaming = calcular_q_streaming(
        metricas=lastfm,
        identidad_confirmada=identidad_confirmada,
        perfil_encontrado=perfil_encontrado,
    )

    return {
        "postulacion_id": postulacion_id,

        "spotify": {
            "id": spotify_id,
            "nombre": spotify["nombre"],
            "url": spotify["url"],
        },

        "lastfm": lastfm,

        "perfil_encontrado": perfil_encontrado,
        "identidad_confirmada": identidad_confirmada,
        "estado": estado,

        "q_streaming": q_streaming,
    }
