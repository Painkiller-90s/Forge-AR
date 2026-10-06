import asyncio
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import UploadFile

from app.services.file_service import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
)


# =========================
# CONFIGURACIÓN HU003
# =========================

MIN_SAMPLE_RATE = 44100

MIN_MP3_BITRATE = 128000  # 128 kbps

MIN_FLAC_BITS_PER_SAMPLE = 16


# =========================
# UTILIDADES
# =========================

def _entero_positivo(valor):
    try:
        numero = int(valor)

        if numero > 0:
            return numero

    except (TypeError, ValueError):
        pass

    return None


def _decimal_positivo(valor):
    try:
        numero = float(valor)

        if numero >= 0:
            return numero

    except (TypeError, ValueError):
        pass

    return None


# =========================
# COMPROBAR FFMPEG
# =========================

def verificar_ffmpeg() -> None:
    if shutil.which("ffprobe") is None:
        raise RuntimeError(
            "FFprobe no está disponible en el sistema."
        )

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg no está disponible en el sistema."
        )


# =========================
# FFPROBE
# =========================

def ejecutar_ffprobe(ruta_archivo: Path) -> dict:
    comando = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(ruta_archivo),
    ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )

    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            "El análisis técnico del archivo excedió el tiempo permitido."
        ) from exc

    if resultado.returncode != 0:
        raise ValueError(
            "El archivo de audio es ilegible, está corrupto "
            "o posee una estructura inválida."
        )

    try:
        return json.loads(
            resultado.stdout
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            "No fue posible interpretar la información técnica del audio."
        ) from exc


# =========================
# VALIDAR DECODIFICACIÓN
# =========================

def validar_decodificacion(
    ruta_archivo: Path
) -> None:
    """
    Intenta decodificar el flujo completo de audio.

    Permite detectar archivos dañados que FFprobe
    podría ser capaz de identificar inicialmente.
    """

    comando = [
        "ffmpeg",
        "-v",
        "error",
        "-xerror",
        "-nostdin",
        "-i",
        str(ruta_archivo),
        "-map",
        "0:a:0",
        "-f",
        "null",
        "-",
    ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )

    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            "La validación del flujo de audio excedió "
            "el tiempo permitido."
        ) from exc

    if resultado.returncode != 0:
        raise ValueError(
            "El archivo contiene errores de audio "
            "o está técnicamente corrupto."
        )


# =========================
# ANALIZAR ARCHIVO
# =========================

def calcular_q_audio(
    formato: str,
    sample_rate_hz: int,
    bitrate_bps: int | None,
    bits_per_sample: int | None,
) -> int:
    """
    Calcula el puntaje técnico Q_audio entre 0 y 100.

    El puntaje considera:
    - 40 % frecuencia de muestreo.
    - 60 % calidad de codificación/resolución.

    Solo debe ejecutarse para archivos que ya hayan
    superado las validaciones técnicas mínimas.
    """

    # =========================
    # SAMPLE RATE - 40 %
    # =========================

    if sample_rate_hz >= 48000:
        puntaje_sample_rate = 100
    else:
        # A esta función solo deberían llegar
        # archivos con mínimo 44.100 Hz.
        puntaje_sample_rate = 90


    # =========================
    # MP3
    # =========================

    if formato == "mp3":

        if bitrate_bps is None:
            raise ValueError(
                "No fue posible calcular Q_audio "
                "sin el bitrate del MP3."
            )

        if bitrate_bps >= 320000:
            puntaje_resolucion = 100

        elif bitrate_bps >= 256000:
            puntaje_resolucion = 90

        elif bitrate_bps >= 192000:
            puntaje_resolucion = 75

        else:
            puntaje_resolucion = 60


    # =========================
    # FLAC
    # =========================

    elif formato == "flac":

        if bits_per_sample is None:
            raise ValueError(
                "No fue posible calcular Q_audio "
                "sin la profundidad de bits del FLAC."
            )

        if bits_per_sample >= 24:
            puntaje_resolucion = 100
        else:
            puntaje_resolucion = 95


    else:
        raise ValueError(
            "Formato no compatible con Q_audio."
        )


    # =========================
    # PUNTAJE FINAL
    # =========================

    q_audio = round(
        (puntaje_sample_rate * 0.40)
        +
        (puntaje_resolucion * 0.60)
    )

    return q_audio

def analizar_archivo_tecnico(
    ruta_archivo: Path,
    extension: str,
) -> dict:

    verificar_ffmpeg()

    informacion = ejecutar_ffprobe(
        ruta_archivo
    )

    streams = informacion.get(
        "streams",
        []
    )

    formato_general = informacion.get(
        "format",
        {}
    )


    # =========================
    # BUSCAR FLUJO DE AUDIO
    # =========================

    audio_stream = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type")
            == "audio"
        ),
        None,
    )


    if audio_stream is None:
        raise ValueError(
            "El archivo no contiene un flujo de audio válido."
        )


    # =========================
    # FORMATO REAL
    # =========================

    codec = (
        audio_stream
        .get("codec_name", "")
        .lower()
    )

    formato_esperado = (
        extension
        .lstrip(".")
        .lower()
    )


    if codec != formato_esperado:
        raise ValueError(
            "El contenido real del archivo no corresponde "
            f"al formato {formato_esperado.upper()} declarado."
        )


    # =========================
    # SAMPLE RATE
    # =========================

    sample_rate_hz = _entero_positivo(
        audio_stream.get(
            "sample_rate"
        )
    )


    if sample_rate_hz is None:
        raise ValueError(
            "No fue posible determinar la frecuencia "
            "de muestreo del audio."
        )


    if sample_rate_hz < MIN_SAMPLE_RATE:
        raise ValueError(
            "La frecuencia de muestreo debe ser "
            "de al menos 44.100 Hz."
        )


    # =========================
    # BITRATE
    # =========================

    bitrate_bps = (
        _entero_positivo(
            audio_stream.get(
                "bit_rate"
            )
        )
        or
        _entero_positivo(
            formato_general.get(
                "bit_rate"
            )
        )
    )


    # =========================
    # BITS POR MUESTRA
    # =========================

    bits_per_sample = (
        _entero_positivo(
            audio_stream.get(
                "bits_per_raw_sample"
            )
        )
        or
        _entero_positivo(
            audio_stream.get(
                "bits_per_sample"
            )
        )
    )


    # =========================
    # VALIDACIÓN MP3
    # =========================

    if formato_esperado == "mp3":

        if bitrate_bps is None:
            raise ValueError(
                "No fue posible determinar el bitrate del archivo MP3."
            )

        if bitrate_bps < MIN_MP3_BITRATE:
            raise ValueError(
                "El archivo MP3 debe tener un bitrate "
                "mínimo de 128 kbps."
            )


    # =========================
    # VALIDACIÓN FLAC
    # =========================

    if formato_esperado == "flac":

        if bits_per_sample is None:
            raise ValueError(
                "No fue posible determinar la profundidad "
                "de bits del archivo FLAC."
            )

        if (
            bits_per_sample
            < MIN_FLAC_BITS_PER_SAMPLE
        ):
            raise ValueError(
                "El archivo FLAC debe tener una profundidad "
                "mínima de 16 bits."
            )


    # =========================
    # OTROS METADATOS
    # =========================

    channels = _entero_positivo(
        audio_stream.get(
            "channels"
        )
    )

    duracion_segundos = (
        _decimal_positivo(
            audio_stream.get(
                "duration"
            )
        )
        or
        _decimal_positivo(
            formato_general.get(
                "duration"
            )
        )
    )

    formato_contenedor = (
        formato_general
        .get(
            "format_name",
            ""
        )
    )


    # =========================
    # COMPROBAR INTEGRIDAD
    # =========================

    validar_decodificacion(
        ruta_archivo
    )

    q_audio = calcular_q_audio(
        formato=formato_esperado,
        sample_rate_hz=sample_rate_hz,
        bitrate_bps=bitrate_bps,
        bits_per_sample=bits_per_sample,
    )

    # =========================
    # RESULTADO
    # =========================

    return {
        "codec": codec,
        "formato_contenedor": formato_contenedor,
        "sample_rate_hz": sample_rate_hz,
        "bitrate_bps": bitrate_bps,
        "bits_per_sample": bits_per_sample,
        "channels": channels,
        "duracion_segundos": duracion_segundos,
        "valido": True,
        "motivos_rechazo": [],
        "q_audio": q_audio,
    }


# =========================
# VALIDAR UPLOAD
# =========================

async def validar_audio(
    archivo: UploadFile
) -> dict:
    """
    Valida técnicamente una demo antes
    de almacenarla en Cloudflare R2.
    """

    if not archivo.filename:
        raise ValueError(
            "El archivo no tiene un nombre válido."
        )


    extension = Path(
        archivo.filename
    ).suffix.lower()


    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Solo se permiten archivos MP3 o FLAC."
        )


    # =========================
    # CREAR ARCHIVO TEMPORAL
    # =========================

    temporal = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as archivo_temporal:

            temporal = Path(
                archivo_temporal.name
            )

            tamano_bytes = 0

            await archivo.seek(0)

            while True:
                chunk = await archivo.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                tamano_bytes += len(
                    chunk
                )

                if (
                    tamano_bytes
                    > MAX_FILE_SIZE
                ):
                    raise ValueError(
                        "El archivo supera el límite "
                        "máximo de 200 MB."
                    )

                archivo_temporal.write(
                    chunk
                )


        if tamano_bytes == 0:
            raise ValueError(
                "El archivo está vacío."
            )


        # =========================
        # ANALIZAR EN OTRO THREAD
        # =========================

        resultado = await asyncio.to_thread(
            analizar_archivo_tecnico,
            temporal,
            extension,
        )


        return resultado


    finally:
        # Dejamos el UploadFile disponible
        # para HU002 / Cloudflare R2.

        await archivo.seek(0)


        # Borrar siempre el archivo temporal.

        if (
            temporal is not None
            and temporal.exists()
        ):
            temporal.unlink()