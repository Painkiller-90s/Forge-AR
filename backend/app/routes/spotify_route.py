
import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.config.database import database
from app.routes.auth_route import get_current_user
from app.services.spotify_service import (
    consultar_artista_spotify,
    consultar_catalogo_spotify,
    extraer_id_artista_spotify,
)
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/postulaciones", tags=["Spotify"])
logger = logging.getLogger(__name__)


@router.get("/{postulacion_id}/spotify")
async def consultar_spotify_postulacion(
    postulacion_id: str,
    current_user: dict = Depends(get_current_user),
):
    # Solo los evaluadores A&R pueden consultar esta información.
    if current_user.get("role") != "ar":
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para consultar Spotify.",
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

    # Garantizar que la postulación pertenece al sello del A&R.
    postulacion = await database.postulaciones.find_one({
        "_id": ObjectId(postulacion_id),
        "sello_id": sello_id,
    })

    if not postulacion:
        raise HTTPException(
            status_code=404,
            detail="Postulación no encontrada.",
        )

    # Obtener el enlace registrado durante la postulación.
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

    # Consultar la API oficial utilizando credenciales del backend.
    try:
        perfil = await consultar_artista_spotify(spotify_id)
        catalogo = await consultar_catalogo_spotify(spotify_id)
    except Exception as exc:
        logger.exception(
            "HU005: Error consultando Spotify para postulación %s",
            postulacion_id,
        )
        raise HTTPException(
            status_code=502,
            detail="No fue posible obtener los datos de Spotify.",
        ) from exc

    return {
        "postulacion_id": str(postulacion["_id"]),
        "spotify_id": spotify_id,
        "perfil": perfil,
        "catalogo": catalogo,
    }


@router.post("/{postulacion_id}/spotify/actualizar")
async def actualizar_spotify_postulacion(
    postulacion_id: str,
    current_user: dict = Depends(get_current_user),
):
    # Reutiliza las validaciones de rol, sello e ID existentes.
    datos = await consultar_spotify_postulacion(
        postulacion_id,
        current_user,
    )

    ahora = datetime.now(timezone.utc)

    registro = {
        "postulacion_id": datos["postulacion_id"],
        "sello_id": current_user["label_id"],
        "spotify_id": datos["spotify_id"],
        "nombre_artista": datos["perfil"]["nombre"],
        "url": datos["perfil"]["url"],
        "seguidores": datos["perfil"]["seguidores"],
        "popularidad": datos["perfil"]["popularidad"],
        "total_lanzamientos": datos["catalogo"]["total_lanzamientos"],
        "fuente": "Spotify Web API",
        "fecha_obtencion": ahora,
        "expires_at": ahora + timedelta(hours=24),
    }

    try:
        # Índice TTL: elimina automáticamente registros vencidos.
        await database.spotify_cache.create_index(
            "expires_at",
            expireAfterSeconds=0,
        )

        await database.spotify_cache.update_one(
            {"postulacion_id": datos["postulacion_id"]},
            {"$set": registro},
            upsert=True,
        )
    except Exception as exc:
        logger.exception(
            "HU005: Error al guardar datos de Spotify para %s",
            postulacion_id,
        )
        raise HTTPException(
            status_code=500,
            detail="No fue posible guardar los datos de Spotify.",
        ) from exc

    return {
        "mensaje": "Consulta de Spotify registrada correctamente.",
        "postulacion_id": datos["postulacion_id"],
        "spotify_id": datos["spotify_id"],
        "fuente": registro["fuente"],
        "fecha_obtencion": ahora,
        "expires_at": registro["expires_at"],
    }
