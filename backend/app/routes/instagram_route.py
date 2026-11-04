
import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.config.database import database
from app.routes.auth_route import get_current_user
from app.services.instagram_service import (
    extraer_usuario_instagram,
    obtener_metricas_instagram,
)


router = APIRouter(
    prefix="/postulaciones",
    tags=["Instagram"]
)

logger = logging.getLogger(__name__)


@router.post("/{postulacion_id}/instagram/consultar")
async def consultar_instagram_postulacion(
    postulacion_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Obtiene métricas públicas de Instagram mediante Apify
    para una postulación autorizada.
    """

    # Solo evaluadores A&R pueden consultar las métricas.
    if current_user.get("role") != "ar":
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para consultar Instagram.",
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

    # Comprobar que la postulación pertenece al sello.
    postulacion = await database.postulaciones.find_one({
        "_id": ObjectId(postulacion_id),
        "sello_id": sello_id,
    })

    if not postulacion:
        raise HTTPException(
            status_code=404,
            detail="Postulación no encontrada.",
        )

    # Recuperar el enlace registrado por el postulante.
    press_kit = postulacion.get("press_kit") or {}
    instagram_url = press_kit.get("instagram_url")

    if not instagram_url:
        raise HTTPException(
            status_code=422,
            detail="La postulación no tiene un enlace de Instagram.",
        )

    # Validar antes de consumir créditos de Apify.
    try:
        extraer_usuario_instagram(instagram_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="El enlace de Instagram no es válido.",
        ) from exc

    # Consultar y normalizar las métricas.
    try:
        metricas = await obtener_metricas_instagram(instagram_url)

    except Exception as exc:
        # Evitar registrar tokens o respuestas completas.
        logger.error(
            "HU006: Falló la consulta de Instagram para %s. Tipo: %s",
            postulacion_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="No fue posible obtener las métricas de Instagram.",
        ) from exc

    return {
        "postulacion_id": str(postulacion["_id"]),
        "instagram": metricas,
        "estado_identidad": "pendiente_verificacion",
    }
