
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.config.database import database
from app.routes.auth_route import get_current_user
from app.services.spotify_service import extraer_id_artista_spotify
from app.services.instagram_service import extraer_usuario_instagram

from app.services.viability_service import (
    calcular_q_audio_postulacion,
    calcular_q_streaming,
    calcular_q_rrss,
    calcular_q_presskit,
    calcular_q_consistencia,
    calcular_score_viabilidad,
)


router = APIRouter(
    prefix="/postulaciones",
    tags=["Viabilidad"],
)


async def _obtener_metricas_guardadas(
    postulacion_id: str,
    sello_id: str,
    plataforma: str,
    cuenta_id: str | None,
) -> dict | None:
    """Obtiene métricas de la cuenta declarada, sin consultar APIs."""

    if not cuenta_id:
        return None

    registro = await database.metricas_externas.find_one({
        "postulacion_id": postulacion_id,
        "sello_id": sello_id,
        "plataforma": plataforma,
        "cuenta_id": cuenta_id,
    })

    if not isinstance(registro, dict):
        return None

    metricas = registro.get("metricas")

    return metricas if isinstance(metricas, dict) else None


@router.get("/{postulacion_id}/viabilidad")
async def consultar_viabilidad_postulacion(
    postulacion_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Calcula la viabilidad a partir de datos almacenados."""

    if current_user.get("role") != "ar":
        raise HTTPException(
            status_code=403,
            detail="Se requieren permisos A&R.",
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

    # Identificadores declarados en el formulario.
    spotify_id = None
    instagram_usuario = None

    try:
        if press_kit.get("spotify_url"):
            spotify_id = extraer_id_artista_spotify(
                press_kit["spotify_url"]
            )
    except ValueError:
        pass

    try:
        if press_kit.get("instagram_url"):
            instagram_usuario = extraer_usuario_instagram(
                press_kit["instagram_url"]
            )
    except ValueError:
        pass

    # Datos históricos de Spotify e Instagram.
    spotify = await _obtener_metricas_guardadas(
        postulacion_id,
        sello_id,
        "spotify",
        spotify_id,
    )

    instagram = await _obtener_metricas_guardadas(
        postulacion_id,
        sello_id,
        "instagram",
        instagram_usuario,
    )

    # Last.fm se almacena por ID de artista de Spotify.
    lastfm = None
    identidad_confirmada = False

    if spotify_id:
        registro_lastfm = await database.lastfm_cache.find_one({
            "_id": spotify_id,
        })

        if isinstance(registro_lastfm, dict):
            lastfm = registro_lastfm

            mbid = lastfm.get("mbid")

            if isinstance(mbid, str) and mbid:
                identidad = (
                    await database.identidades_artistas.find_one({
                        "_id": spotify_id,
                        "musicbrainz_mbid": mbid,
                        "identidad_confirmada": True,
                    })
                )

                identidad_confirmada = identidad is not None

    # Adaptar la información al formato de las funciones
    # de Q_consistencia.
    respuesta_lastfm = (
        {
            "lastfm": lastfm,
            "identidad_confirmada": identidad_confirmada,
            "estado": (
                "verificada"
                if identidad_confirmada
                else "pendiente_verificacion"
            ),
        }
        if lastfm is not None
        else None
    )

    respuesta_instagram = (
        {"instagram": instagram}
        if instagram is not None
        else None
    )

    # Calcular las cinco dimensiones.
    try:
        q_audio = calcular_q_audio_postulacion(
            postulacion.get("demos") or []
        )

        q_streaming = (
            calcular_q_streaming(
                metricas=lastfm,
                identidad_confirmada=identidad_confirmada,
            )
            if lastfm is not None
            else None
        )

        q_rrss = (
            calcular_q_rrss(instagram)
            if instagram is not None
            else None
        )

        q_presskit = calcular_q_presskit(press_kit)

        q_consistencia = calcular_q_consistencia(
            postulacion,
            spotify,
            respuesta_lastfm,
            respuesta_instagram,
        )

        viabilidad = calcular_score_viabilidad(
            q_audio=q_audio,
            q_streaming=q_streaming,
            q_rrss=q_rrss,
            q_presskit=q_presskit,
            q_consistencia=q_consistencia,
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Existen datos almacenados incompatibles con la evaluación.",
        ) from exc

    return {
        "postulacion_id": postulacion_id,
        "viabilidad": viabilidad,
        "fuentes": {
            "spotify": {
                "disponible": spotify is not None,
                "fecha_obtencion": (
                    spotify.get("fecha_obtencion")
                    if spotify else None
                ),
            },
            "lastfm": {
                "disponible": lastfm is not None,
                "identidad_confirmada": identidad_confirmada,
                "fecha_obtencion": (
                    lastfm.get("fecha_obtencion")
                    if lastfm else None
                ),
            },
            "instagram": {
                "disponible": instagram is not None,
                "fecha_obtencion": (
                    instagram.get("fecha_obtencion")
                    if instagram else None
                ),
            },
        },
    }
