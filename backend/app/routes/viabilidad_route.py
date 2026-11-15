
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.config.database import database
from app.routes.auth_route import get_current_user
from app.utils.evaluacion_response import (
    serializar_datos_utilizados,
)


router = APIRouter(
    prefix="/postulaciones",
    tags=["Viabilidad"],
)


@router.get("/{postulacion_id}/viabilidad")
async def consultar_viabilidad_postulacion(
    postulacion_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Consulta el último reporte de viabilidad generado."""

    # 1. Validar permisos del evaluador.
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

    # 2. Validar identificador.
    if not ObjectId.is_valid(postulacion_id):
        raise HTTPException(
            status_code=400,
            detail="ID de postulación inválido.",
        )

    # 3. Recuperar el último reporte del sello autorizado.
    reporte = await database.evaluaciones.find_one(
        {
            "postulacion_id": postulacion_id,
            "sello_id": str(sello_id),
        },
        sort=[("fecha_generacion", -1)],
    )

    if not reporte:
        raise HTTPException(
            status_code=404,
            detail="No existe una evaluación generada para esta postulación.",
        )

    # 4. Preparar información de viabilidad.
    viabilidad = reporte.get("viabilidad") or {}

    # 5. Devolver el reporte con trazabilidad.
    return {
        "evaluacion_id": str(reporte["_id"]),
        "postulacion_id": reporte["postulacion_id"],
        "fecha_generacion": reporte.get("fecha_generacion"),
        "estado": (
            reporte.get("estado")
            or viabilidad.get("estado")
        ),
        "viabilidad": viabilidad,
        "fuentes": reporte.get("fuentes") or {},
        "datos_utilizados": serializar_datos_utilizados(
            reporte.get("datos_utilizados")
        ),
    }
