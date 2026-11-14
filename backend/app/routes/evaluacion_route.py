
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.config.database import client, database
from app.routes.auth_route import get_current_user

from app.services.evaluacion_service import (
    generar_evaluacion_actual,
)

from app.services.audit_service import (
    registrar_auditoria,
)


router = APIRouter(
    prefix="/postulaciones",
    tags=["Evaluaciones"],
)


@router.post(
    "/{postulacion_id}/evaluacion",
    status_code=201,
)
async def generar_reporte_evaluacion(
    postulacion_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Genera y almacena un reporte de evaluación."""

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

    # 2. Validar identificador de postulación.
    if not ObjectId.is_valid(postulacion_id):
        raise HTTPException(
            status_code=400,
            detail="ID de postulación inválido.",
        )

    # 3. Generar evaluación utilizando HU008.
    # Las consultas externas y los cálculos ocurren
    # antes de iniciar la transacción.
    try:
        evaluacion = await generar_evaluacion_actual(
            postulacion_id=postulacion_id,
            sello_id=sello_id,
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=500,
            detail="No fue posible calcular la evaluación.",
        ) from exc

    if evaluacion is None:
        raise HTTPException(
            status_code=404,
            detail="Postulación no encontrada.",
        )

    # 4. Construir el reporte.
    fecha_generacion = datetime.now(timezone.utc)

    # Generar el identificador antes de iniciar
    # la transacción para mantenerlo estable ante reintentos.
    evaluacion_id_obj = ObjectId()
    evaluacion_id = str(evaluacion_id_obj)

    reporte = {
        "_id": evaluacion_id_obj,
        "postulacion_id": postulacion_id,
        "sello_id": str(sello_id),
        "evaluador_id": str(current_user["_id"]),
        "fecha_generacion": fecha_generacion,
        "estado": evaluacion["viabilidad"]["estado"],
        "viabilidad": evaluacion["viabilidad"],
        "fuentes": evaluacion["fuentes"],
        "datos_utilizados": evaluacion["datos_utilizados"],
    }

    # 5. Guardar reporte y auditoría en una
    # única transacción de MongoDB.
    async def guardar_reporte_y_auditoria(session):

        # Insertar el reporte.
        await database.evaluaciones.insert_one(reporte)

        # Registrar la auditoría.
        # La sesión está vinculada automáticamente
        # a esta operación mediante session.bind().
        await registrar_auditoria(
            usuario=current_user,
            sello_id=sello_id,
            postulacion_id=postulacion_id,
            recurso="evaluacion",
            recurso_id=evaluacion_id,
            accion="GENERACION_EVALUACION",
            metodo="generar",
        )

        return evaluacion_id

    try:
        async with client.start_session().bind() as session:

            await session.with_transaction(
                guardar_reporte_y_auditoria
            )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible guardar el reporte "
                "y registrar su auditoría."
            ),
        ) from exc

    # 6. Devolver reporte confirmado.
    return {
        "evaluacion_id": evaluacion_id,
        "postulacion_id": postulacion_id,
        "fecha_generacion": fecha_generacion,
        "estado": reporte["estado"],
        "viabilidad": reporte["viabilidad"],
        "fuentes": reporte["fuentes"],
        "datos_utilizados": reporte["datos_utilizados"],
    }
