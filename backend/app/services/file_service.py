import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import re

import boto3
from fastapi import UploadFile

from app.config.settings import settings


# =========================
# CONFIGURACIÓN
# =========================

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB

ALLOWED_EXTENSIONS = {
    ".mp3",
    ".flac",
}

MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".flac": "audio/flac",
}


# =========================
# CLIENTE CLOUDFLARE R2
# =========================

def obtener_cliente_r2():
    return boto3.client(
        "s3",
        endpoint_url=(
            f"https://{settings.r2_account_id}"
            ".r2.cloudflarestorage.com"
        ),
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


# =========================
# GUARDAR DEMO
# =========================

async def guardar_demo(archivo: UploadFile) -> dict:
    """
    Valida una demo musical y la almacena
    en Cloudflare R2.
    """

    # -------------------------
    # Validar nombre
    # -------------------------

    if not archivo.filename:
        raise ValueError(
            "El archivo no tiene un nombre válido."
        )

    # -------------------------
    # Validar extensión
    # -------------------------

    extension = Path(
        archivo.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Solo se permiten archivos MP3 o FLAC."
        )

    # MIME normalizado según extensión válida
    mime_type = MIME_TYPES[extension]

    # -------------------------
    # Calcular tamaño y SHA-256
    # -------------------------

    tamano_bytes = 0
    sha256 = hashlib.sha256()

    await archivo.seek(0)

    while True:
        chunk = await archivo.read(
            1024 * 1024
        )

        if not chunk:
            break

        tamano_bytes += len(chunk)

        if tamano_bytes > MAX_FILE_SIZE:
            raise ValueError(
                "El archivo supera el límite máximo de 200 MB."
            )

        sha256.update(chunk)

    # -------------------------
    # Validar archivo vacío
    # -------------------------

    if tamano_bytes == 0:
        raise ValueError(
            "El archivo está vacío."
        )

    # -------------------------
    # Generar identificadores
    # -------------------------

    archivo_id = uuid4().hex

    storage_key = (
        f"demos/{archivo_id}{extension}"
    )

    # -------------------------
    # Volver al inicio del archivo
    # -------------------------

    await archivo.seek(0)

    # -------------------------
    # Subir a Cloudflare R2
    # -------------------------

    cliente_r2 = obtener_cliente_r2()

    extra_args = {
        "ContentType": mime_type,
        "Metadata": {
            "archivo-id": archivo_id,
            "sha256": sha256.hexdigest(),
        },
    }

    try:
        await asyncio.to_thread(
            cliente_r2.upload_fileobj,
            archivo.file,
            settings.r2_bucket_name,
            storage_key,
            ExtraArgs=extra_args,
        )

    except Exception as exc:
        raise RuntimeError(
            "No fue posible almacenar la demo en Cloudflare R2."
        ) from exc

    # -------------------------
    # Metadatos
    # -------------------------

    return {
        "archivo_id": archivo_id,
        "nombre_archivo": archivo.filename,
        "formato": extension.lstrip("."),
        "tamano_bytes": tamano_bytes,
        "mime_type": mime_type,
        "sha256": sha256.hexdigest(),
        "storage_key": storage_key,
        "uploaded_at": datetime.now(
            timezone.utc
        ),
    }


# =========================
# ELIMINAR DEMO
# =========================

async def eliminar_demo(storage_key: str) -> None:
    """
    Elimina una demo de Cloudflare R2.

    Se utilizará para limpiar los archivos
    si falla la creación de la postulación.
    """

    cliente_r2 = obtener_cliente_r2()

    await asyncio.to_thread(
        cliente_r2.delete_object,
        Bucket=settings.r2_bucket_name,
        Key=storage_key,
    )


# ==========================================
# HU004 - LECTURA PRIVADA DE DEMOS
# ==========================================

async def obtener_demo_privada(
    storage_key: str,
    rango: str | None = None,
) -> dict:
    """
    Obtiene un archivo desde Cloudflare R2 sin
    generar una URL pública ni una URL firmada.

    Permite obtener el archivo completo o un
    rango de bytes para reproducción de audio.

    IMPORTANTE:
    La autorización del usuario debe verificarse
    antes de ejecutar esta función.
    """

    # Validar la clave de almacenamiento
    if not storage_key:
        raise ValueError(
            "La clave de almacenamiento es obligatoria."
        )

    # Las demos se almacenan con UUID hexadecimal
    # y extensión MP3 o FLAC.
    patron = r"demos/[0-9a-f]{32}\.(mp3|flac)"

    if not re.fullmatch(patron, storage_key):
        raise ValueError(
            "La clave de almacenamiento no es válida."
        )

    # Preparar solicitud a R2
    parametros = {
        "Bucket": settings.r2_bucket_name,
        "Key": storage_key,
    }

    # El rango debe haber sido validado
    # previamente por el endpoint.
    if rango is not None:
        parametros["Range"] = rango

    # Obtener cliente privado de R2
    cliente_r2 = obtener_cliente_r2()

    # boto3 es síncrono: ejecutarlo en otro hilo
    respuesta = await asyncio.to_thread(
        cliente_r2.get_object,
        **parametros,
    )

    # No leemos el archivo completo aquí.
    # Body contiene un flujo que el endpoint
    # consumirá por partes y deberá cerrar.
    return respuesta
