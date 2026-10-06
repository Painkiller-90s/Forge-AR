from typing import Annotated
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import ValidationError

from app.config.database import database
from app.models.postulacion_model import postulacion_document
from app.schemas.postulacion_schema import (
    PostulacionCreate,
    PostulacionResponse,
)
from app.services.file_service import (
    eliminar_demo,
    guardar_demo,
)

from app.services.audio_validation_service import validar_audio

router = APIRouter(
    prefix="/postulaciones",
    tags=["Postulaciones"]
)


# =========================
# SERIALIZACIÓN
# =========================

def serialize_postulacion(postulacion: dict) -> dict:
    return {
        "id": str(postulacion["_id"]),
        "sello_id": postulacion["sello_id"],
        "nombre_artistico": postulacion["press_kit"]["nombre_artistico"],
        "correo_contacto": postulacion["press_kit"]["correo_contacto"],
        "demos": [
            {
                "archivo_id": demo["archivo_id"],
                "nombre": demo["nombre"],
                "nombre_archivo": demo["nombre_archivo"],
                "formato": demo["formato"],
                "tamano_bytes": demo["tamano_bytes"],
                "mime_type": demo.get("mime_type"),
                "sha256": demo["sha256"],
                "uploaded_at": demo["uploaded_at"],

                "audio_tecnico": demo["audio_tecnico"],

                "validacion_tecnica": demo["validacion_tecnica"],
            }
            for demo in postulacion["demos"]
        ],
        "estado": postulacion["estado"],
    }


# =========================
# LIMPIEZA DE R2
# =========================

async def limpiar_demos(demos: list[dict]) -> None:
    """
    Elimina de R2 las demos que ya fueron
    subidas si ocurre un error posterior.
    """

    for demo in demos:
        try:
            await eliminar_demo(
                demo["storage_key"]
            )
        except Exception:
            # No ocultamos el error original
            # si la limpieza también falla.
            pass


# =========================
# CREAR POSTULACIÓN
# =========================

@router.post(
    "/{sello_id}",
    response_model=PostulacionResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear_postulacion(
    sello_id: str,
    postulacion: Annotated[str, Form()],
    archivos: Annotated[list[UploadFile], File()],
):
    # -------------------------
    # Validar sello
    # -------------------------

    if not sello_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El sello es obligatorio"
        )

    # -------------------------
    # Convertir JSON a schema
    # -------------------------

    try:
        datos_postulacion = (
            PostulacionCreate.model_validate_json(
                postulacion
            )
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors()
        ) from exc

    # -------------------------
    # Validar cantidad archivos
    # -------------------------

    if not 1 <= len(archivos) <= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Debes cargar entre 1 y 3 "
                "archivos de audio."
            )
        )

    # Cada nombre de canción debe
    # corresponder a un archivo.
    if len(archivos) != len(
        datos_postulacion.demos
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "La cantidad de demos no coincide "
                "con la cantidad de archivos enviados."
            )
        )

    # -------------------------
    # Subir demos a R2
    # -------------------------

    demos_guardadas = []

    try:
        for demo, archivo in zip(
            datos_postulacion.demos,
            archivos
        ):
            # HU003:
            # validar técnicamente antes de almacenar
            audio_tecnico = await validar_audio(
                archivo
            )

            # HU002:
            # almacenar solamente si pasó la validación
            metadatos = await guardar_demo(
                archivo
            )

            demos_guardadas.append({
                "nombre": demo.nombre,
                **metadatos,
                "audio_tecnico": audio_tecnico,
            })

    except ValueError as exc:
        await limpiar_demos(
            demos_guardadas
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        await limpiar_demos(
            demos_guardadas
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible almacenar "
                "las demos."
            )
        ) from exc

    # -------------------------
    # Preparar documento Mongo
    # -------------------------

    data = datos_postulacion.model_dump()

    # Reemplazamos los demos básicos
    # por los demos con metadatos R2.
    data["demos"] = demos_guardadas

    document = postulacion_document(
        data=data,
        sello_id=sello_id.strip()
    )

    # -------------------------
    # Guardar en MongoDB
    # -------------------------

    try:
        result = await database.postulaciones.insert_one(
            document
        )

    except Exception as exc:
        # Si Mongo falla, eliminamos los
        # archivos que alcanzaron a subir a R2.
        await limpiar_demos(
            demos_guardadas
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible registrar "
                "la postulación."
            )
        ) from exc

    # -------------------------
    # Recuperar postulación
    # -------------------------

    creada = await database.postulaciones.find_one(
        {"_id": result.inserted_id}
    )

    if not creada:
        # Evitamos dejar tanto un documento
        # como archivos huérfanos.
        await database.postulaciones.delete_one(
            {"_id": result.inserted_id}
        )

        await limpiar_demos(
            demos_guardadas
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No se pudo recuperar "
                "la postulación creada."
            )
        )

    return serialize_postulacion(
        creada
    )