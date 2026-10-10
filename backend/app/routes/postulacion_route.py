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
import re

from fastapi import Request
from fastapi.responses import StreamingResponse
from botocore.exceptions import ClientError
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

import asyncio
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import Depends, Response

from app.routes.auth_route import get_current_user
from app.services.file_service import obtener_demo_privada


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



# ==========================================
# HU004 - STREAMING PROTEGIDO DE DEMOS
# ==========================================

@router.get(
    "/{postulacion_id}/demos/{archivo_id}/stream"
)
async def reproducir_demo(
    postulacion_id: str,
    archivo_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):

    # 1. Verificar rol del usuario
    if current_user.get("role") not in ("ar", "admin"):
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a las demos."
        )

    # 2. Verificar sello asignado
    label_id = current_user.get("label_id")

    if not label_id:
        raise HTTPException(
            status_code=403,
            detail="El usuario no tiene un sello asignado."
        )

    # 3. Validar ID de postulación
    if not ObjectId.is_valid(postulacion_id):
        raise HTTPException(
            status_code=400,
            detail="ID de postulación inválido."
        )

    # 4. Buscar postulación
    postulacion = await database.postulaciones.find_one({
        "_id": ObjectId(postulacion_id)
    })

    if not postulacion:
        raise HTTPException(
            status_code=404,
            detail="Postulación no encontrada."
        )

    # 5. Verificar pertenencia al sello
    if str(label_id) != str(postulacion["sello_id"]):
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a esta postulación."
        )

    # 6. Buscar demo autorizada
    demo = next(
        (
            item
            for item in postulacion.get("demos", [])
            if item.get("archivo_id") == archivo_id
        ),
        None,
    )

    if not demo:
        raise HTTPException(
            status_code=404,
            detail="Demo no encontrada."
        )

    # 7. Obtener tamaño y validar solicitud Range
    tamano = demo["tamano_bytes"]
    rango_solicitado = request.headers.get("range")
    rango_r2 = None
    inicio = None
    fin = None

    def rango_invalido():
        raise HTTPException(
            status_code=416,
            detail="Rango de bytes no válido.",
            headers={
                "Content-Range": f"bytes */{tamano}"
            },
        )

    if rango_solicitado is not None:

        coincidencia = re.fullmatch(
            r"bytes=(\d*)-(\d*)",
            rango_solicitado.strip(),
        )

        if not coincidencia or tamano <= 0:
            rango_invalido()

        inicio_texto, fin_texto = coincidencia.groups()

        if not inicio_texto and not fin_texto:
            rango_invalido()

        if inicio_texto:
            inicio = int(inicio_texto)
            fin = (
                int(fin_texto)
                if fin_texto
                else tamano - 1
            )
            fin = min(fin, tamano - 1)

            if inicio >= tamano or fin < inicio:
                rango_invalido()

        else:
            # Soporta rangos de sufijo: bytes=-1024
            cantidad = int(fin_texto)

            if cantidad <= 0:
                rango_invalido()

            inicio = max(0, tamano - cantidad)
            fin = tamano - 1

        rango_r2 = f"bytes={inicio}-{fin}"

    # 8. Obtener flujo privado desde R2
    try:
        objeto = await obtener_demo_privada(
            demo["storage_key"],
            rango_r2,
        )

    except ClientError as exc:
        codigo = exc.response.get(
            "Error", {}
        ).get("Code")

        if codigo in ("NoSuchKey", "404"):
            raise HTTPException(
                status_code=404,
                detail="Archivo no encontrado en almacenamiento."
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="No fue posible obtener la demo desde R2."
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="No fue posible obtener la demo desde R2."
        ) from exc

    cuerpo = objeto["Body"]

    # 9. Registrar acceso autorizado
    try:
        await database.auditorias.insert_one({
            "usuario_id": str(current_user["_id"]),
            "rol": current_user["role"],
            "sello_id": postulacion["sello_id"],
            "postulacion_id": str(postulacion["_id"]),
            "recurso": "demo",
            "recurso_id": archivo_id,
            "accion": "ACCESO_DEMO_AUTORIZADO",
            "metodo": "stream",
            "fecha": datetime.now(timezone.utc),
        })

    except Exception as exc:
        await asyncio.to_thread(cuerpo.close)

        raise HTTPException(
            status_code=500,
            detail="No fue posible registrar el acceso."
        ) from exc

    # 10. Transmitir audio por fragmentos
    async def transmitir_audio():
        try:
            while True:
                fragmento = await asyncio.to_thread(
                    cuerpo.read,
                    1024 * 1024,
                )

                if not fragmento:
                    break

                yield fragmento

        finally:
            await asyncio.to_thread(cuerpo.close)

    # 11. Preparar respuesta
    formato = demo["formato"]

    mime_type = {
        "mp3": "audio/mpeg",
        "flac": "audio/flac",
    }.get(formato, "application/octet-stream")

    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Content-Disposition": (
            f'inline; filename="demo.{formato}"'
        ),
    }

    codigo_http = 200

    if rango_r2 is not None:
        codigo_http = 206

        headers["Content-Range"] = (
            f"bytes {inicio}-{fin}/{tamano}"
        )

        headers["Content-Length"] = str(
            fin - inicio + 1
        )

    else:
        headers["Content-Length"] = str(
            objeto["ContentLength"]
        )

    return StreamingResponse(
        transmitir_audio(),
        status_code=codigo_http,
        media_type=mime_type,
        headers=headers,
    )

