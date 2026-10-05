from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# =========================
# DEMO
# =========================

class DemoCreate(BaseModel):
    nombre: str = Field(
        min_length=1,
        max_length=150
    )


# =========================
# POSTULACIÓN
# =========================

class PostulacionCreate(BaseModel):

    nombre_artistico: str = Field(
        min_length=2,
        max_length=100
    )

    correo_contacto: EmailStr

    pais: str = Field(
        min_length=2,
        max_length=100
    )

    tipo_proyecto: str = Field(
        min_length=2,
        max_length=50
    )

    generos: list[str] = Field(
        min_length=1,
        max_length=10
    )

    biografia: str = Field(
        min_length=10,
        max_length=3000
    )

    # HU002:
    # mínimo 1 demo y máximo 3
    demos: list[DemoCreate] = Field(
        min_length=1,
        max_length=3
    )

    # =========================
    # CAMPOS OPCIONALES
    # =========================

    integrantes: list[str] = Field(
        default_factory=list,
        max_length=30
    )

    ciudad: str | None = Field(
        default=None,
        max_length=100
    )

    anio_inicio: int | None = Field(
        default=None,
        ge=1900,
        le=2100
    )

    spotify_url: str | None = Field(
        default=None,
        max_length=500
    )

    instagram_url: str | None = Field(
        default=None,
        max_length=500
    )

    mensaje_sello: str | None = Field(
        default=None,
        max_length=2000
    )

    # Ambos consentimientos deben ser obligatoriamente True
    consentimiento_datos: Literal[True]

    autorizacion_demo: Literal[True]


# =========================
# RESPUESTA DE UNA DEMO
# =========================

class DemoResponse(BaseModel):
    archivo_id: str
    nombre: str
    nombre_archivo: str
    formato: str
    tamano_bytes: int
    mime_type: str | None
    sha256: str
    uploaded_at: datetime


# =========================
# RESPUESTA DE POSTULACIÓN
# =========================

class PostulacionResponse(BaseModel):
    id: str
    sello_id: str
    nombre_artistico: str
    correo_contacto: EmailStr
    demos: list[DemoResponse]
    estado: str