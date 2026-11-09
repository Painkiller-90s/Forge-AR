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


class AudioTecnicoResponse(BaseModel):
    codec: str
    formato_contenedor: str
    sample_rate_hz: int
    bitrate_bps: int | None
    bits_per_sample: int | None
    channels: int | None
    duracion_segundos: float | None


class ValidacionTecnicaResponse(BaseModel):
    valido: bool
    motivos_rechazo: list[str]
    q_audio: int


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

    audio_tecnico: AudioTecnicoResponse | None = None
    validacion_tecnica: ValidacionTecnicaResponse | None = None


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



# =========================
# HU012 - DETALLE DEL PRESS KIT
# =========================

class PressKitResponse(BaseModel):
    nombre_artistico: str
    correo_contacto: EmailStr
    pais: str
    ciudad: str | None = None
    tipo_proyecto: str
    generos: list[str] = Field(default_factory=list)
    integrantes: list[str] = Field(default_factory=list)
    biografia: str
    anio_inicio: int | None = None
    spotify_url: str | None = None
    instagram_url: str | None = None
    mensaje_sello: str | None = None


class DetallePostulacionResponse(PostulacionResponse):
    press_kit: PressKitResponse
    created_at: datetime
    updated_at: datetime


# =========================
# HU011 - BANDEJA DE POSTULACIONES
# =========================

class BandejaPostulacionResponse(BaseModel):
    id: str
    nombre_artistico: str
    pais: str
    ciudad: str | None = None
    tipo_proyecto: str
    generos: list[str]
    estado: str
    created_at: datetime


class BandejaPostulacionesResponse(BaseModel):
    postulaciones: list[BandejaPostulacionResponse]
    generos_disponibles: list[str]
    total: int

# =========================
# HU012 - TOKEN DE REPRODUCCIÓN
# =========================

class DemoPlaybackTokenResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    expires_in: int