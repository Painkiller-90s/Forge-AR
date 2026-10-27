import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.config.database import database
from app.routes.auth_route import get_current_user
from app.services.spotify_service import (
    consultar_artista_spotify,
    extraer_id_artista_spotify,
)
from app.services.lastfm_service import consultar_artista_lastfm
from app.services.artist_identity_service import verificar_identidad_con_cache


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

    # Evitar consultar postulaciones de otros sellos.
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

    try:
        spotify_id = extraer_id_artista_spotify(spotify_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="El enlace de Spotify no es válido.",
        ) from exc

    try:
        # Spotify proporciona el nombre del perfil vinculado.
        spotify = await consultar_artista_spotify(spotify_id)

        # Last.fm devuelve las estadísticas del nombre consultado.
        lastfm = await consultar_artista_lastfm(spotify["nombre"])

    except Exception as exc:
        logger.exception(
            "HU005: Error al consultar métricas para %s",
            postulacion_id,
        )
        raise HTTPException(
            status_code=502,
            detail="No fue posible consultar las métricas externas.",
        ) from exc

    # Verificar correspondencia entre Last.fm y Spotify.
    try:
        identidad_confirmada = await verificar_identidad_con_cache(
            lastfm.get("mbid"),
            spotify_id,
        )

        estado = (
            "verificada"
            if identidad_confirmada
            else "pendiente_verificacion"
        )

    except Exception:
        logger.exception(
            "HU005: No fue posible verificar la identidad en MusicBrainz "
            "para la postulación %s",
            postulacion_id,
        )

        identidad_confirmada = False
        estado = "verificacion_no_disponible"

    # La coincidencia de nombres no prueba identidad por sí sola.
    return {
        "postulacion_id": postulacion_id,
        "spotify": {
            "id": spotify_id,
            "nombre": spotify["nombre"],
            "url": spotify["url"],
        },
        "lastfm": lastfm,
        "identidad_confirmada": identidad_confirmada,
        "estado": estado,   
    }
