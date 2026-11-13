
import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.config.database import database
from app.routes.auth_route import get_current_user

from app.services.instagram_service import (
    extraer_usuario_instagram,
    obtener_metricas_instagram,
)

from app.services.metricas_cache_service import (
    guardar_metricas_validas,
    recuperar_ultimas_metricas,
)

from app.services.viability_service import calcular_q_rrss


router = APIRouter(
    prefix="/postulaciones",
    tags=["Instagram"],
)

logger = logging.getLogger(__name__)


@router.post("/{postulacion_id}/instagram/consultar")
async def consultar_instagram_postulacion(
    postulacion_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Consulta métricas públicas de Instagram para una
    postulación autorizada y calcula Q_rrss.
    """

    # Solo los evaluadores A&R pueden consultar las métricas.
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

    # Obtener el enlace registrado por el artista.
    press_kit = postulacion.get("press_kit") or {}
    instagram_url = press_kit.get("instagram_url")

    if not instagram_url:
        raise HTTPException(
            status_code=422,
            detail="La postulación no tiene un enlace de Instagram.",
        )

    # Validar la URL antes de consultar Apify.
    try:
        usuario_instagram = extraer_usuario_instagram(instagram_url)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="El enlace de Instagram no es válido.",
        ) from exc

    # Consultar y normalizar las métricas de Instagram.
    try:
        metricas = await obtener_metricas_instagram(instagram_url)

    except Exception as exc:
        logger.error(
            "HU007: Falló Instagram para %s. Tipo: %s",
            postulacion_id,
            type(exc).__name__,
        )

        # Recuperar las últimas métricas válidas desde MongoDB.
        try:
            respaldo = await recuperar_ultimas_metricas(
                postulacion_id=str(postulacion["_id"]),
                sello_id=sello_id,
                plataforma="instagram",
                cuenta_id=usuario_instagram,
            )

        except Exception as cache_exc:
            logger.error(
                "HU007: Falló la recuperación del respaldo "
                "para %s. Tipo: %s",
                postulacion_id,
                type(cache_exc).__name__,
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "No fue posible consultar Instagram "
                    "ni recuperar el respaldo."
                ),
            ) from cache_exc

        # Sin respaldo, no es posible realizar la evaluación.
        if respaldo is None:
            raise HTTPException(
                status_code=502,
                detail="No fue posible obtener las métricas de Instagram.",
            ) from exc

        # HU008: calcular Q_rrss con los datos de respaldo.
        q_rrss = calcular_q_rrss(respaldo)

        return {
            "postulacion_id": str(postulacion["_id"]),
            "instagram": respaldo,
            "estado_identidad": "pendiente_verificacion",
            "q_rrss": q_rrss,
        }

    # HU007: guardar las nuevas métricas válidas.
    try:
        await guardar_metricas_validas(
            postulacion_id=str(postulacion["_id"]),
            sello_id=sello_id,
            plataforma="instagram",
            cuenta_id=usuario_instagram,
            metricas=metricas,
        )

    except Exception as exc:
        logger.error(
            "HU007: Error guardando métricas de Instagram "
            "para %s. Tipo: %s",
            postulacion_id,
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail="No fue posible guardar las métricas de Instagram.",
        ) from exc

    # HU008: calcular Q_rrss con las métricas actualizadas.
    q_rrss = calcular_q_rrss(metricas)

    return {
        "postulacion_id": str(postulacion["_id"]),
        "instagram": metricas,
        "estado_identidad": "pendiente_verificacion",
        "q_rrss": q_rrss,
    }
