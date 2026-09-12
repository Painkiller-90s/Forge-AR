from fastapi import APIRouter, HTTPException, status

from app.config.database import database
from app.models.postulacion_model import postulacion_document
from app.schemas.postulacion_schema import (
    PostulacionCreate,
    PostulacionResponse,
)


router = APIRouter(
    prefix="/postulaciones",
    tags=["Postulaciones"]
)


def serialize_postulacion(postulacion: dict) -> dict:
    return {
        "id": str(postulacion["_id"]),
        "sello_id": postulacion["sello_id"],
        "nombre_artistico": postulacion["press_kit"]["nombre_artistico"],
        "correo_contacto": postulacion["press_kit"]["correo_contacto"],
        "nombre_demo": postulacion["demo"]["nombre"],
        "estado": postulacion["estado"],
    }


@router.post(
    "/{sello_id}",
    response_model=PostulacionResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear_postulacion(
    sello_id: str,
    postulacion: PostulacionCreate
):
    if not sello_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El sello es obligatorio"
        )

    data = postulacion.model_dump()

    document = postulacion_document(
        data=data,
        sello_id=sello_id.strip()
    )

    result = await database.postulaciones.insert_one(
        document
    )

    creada = await database.postulaciones.find_one(
        {"_id": result.inserted_id}
    )

    if not creada:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo recuperar la postulación creada"
        )

    return serialize_postulacion(creada)