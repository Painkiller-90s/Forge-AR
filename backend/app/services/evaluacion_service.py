
from bson import ObjectId

from app.config.database import database

from app.services.recopilacion_evaluacion_service import (
    recopilar_metricas_evaluacion,
)

from app.services.viability_service import (
    calcular_q_audio_postulacion,
    calcular_q_streaming,
    calcular_q_rrss,
    calcular_q_presskit,
    calcular_q_consistencia,
    calcular_score_viabilidad,
)


async def generar_evaluacion_actual(
    postulacion_id: str,
    sello_id: str,
) -> dict | None:
    """
    Genera una evaluación completa utilizando HU008 y HU009.

    Primero recopila automáticamente las métricas externas.
    Después calcula las cinco dimensiones de viabilidad.

    No genera consultas HTTP desde este servicio:
    esa responsabilidad pertenece al coordinador.
    """

    # 1. Recuperar la postulación autorizada.
    postulacion = await database.postulaciones.find_one({
        "_id": ObjectId(postulacion_id),
        "sello_id": sello_id,
    })

    if not postulacion:
        return None

    press_kit = postulacion.get("press_kit") or {}
    demos = postulacion.get("demos") or []

    # 2. Recopilar automáticamente las métricas externas.
    recopilacion = await recopilar_metricas_evaluacion(
        postulacion_id=postulacion_id,
        sello_id=sello_id,
    )

    if recopilacion is None:
        return None

    spotify = recopilacion["spotify"]
    instagram = recopilacion["instagram"]
    lastfm = recopilacion["lastfm"]

    identidad_confirmada = recopilacion[
        "identidad_confirmada"
    ]

    perfil_lastfm_encontrado = recopilacion[
        "perfil_lastfm_encontrado"
    ]

    # 3. Preparar las respuestas para Q_consistencia.
    respuesta_lastfm = (
        {
            "lastfm": lastfm,
            "identidad_confirmada": identidad_confirmada,
            "estado": (
                "verificada"
                if identidad_confirmada
                else "pendiente_verificacion"
            ),
        }
        if lastfm is not None
        else None
    )

    respuesta_instagram = (
        {"instagram": instagram}
        if instagram is not None
        else None
    )

    # 4. Calcular las cinco dimensiones de viabilidad.

    q_audio = calcular_q_audio_postulacion(demos)

    # Last.fm puede devolver 0 si confirma que el artista
    # no existe. Una interrupción sin respaldo devuelve None.
    if perfil_lastfm_encontrado is False:
        q_streaming = calcular_q_streaming(
            metricas=None,
            identidad_confirmada=False,
            perfil_encontrado=False,
        )

    elif lastfm is not None:
        q_streaming = calcular_q_streaming(
            metricas=lastfm,
            identidad_confirmada=identidad_confirmada,
            perfil_encontrado=True,
        )

    else:
        q_streaming = None

    q_rrss = (
        calcular_q_rrss(instagram)
        if instagram is not None
        else None
    )

    q_presskit = calcular_q_presskit(press_kit)

    q_consistencia = calcular_q_consistencia(
        postulacion,
        spotify,
        respuesta_lastfm,
        respuesta_instagram,
    )

    # 5. Calcular el Score general.
    viabilidad = calcular_score_viabilidad(
        q_audio=q_audio,
        q_streaming=q_streaming,
        q_rrss=q_rrss,
        q_presskit=q_presskit,
        q_consistencia=q_consistencia,
    )

    # 6. Preparar el resumen de las fuentes.
    fuentes = {
        "spotify": {
            "disponible": spotify is not None,
            "fecha_obtencion": (
                spotify.get("fecha_obtencion")
                if spotify else None
            ),
        },
        "lastfm": {
            "disponible": lastfm is not None,
            "identidad_confirmada": identidad_confirmada,
            "perfil_encontrado": perfil_lastfm_encontrado,
            "fecha_obtencion": (
                lastfm.get("fecha_obtencion")
                if lastfm else None
            ),
        },
        "instagram": {
            "disponible": instagram is not None,
            "fecha_obtencion": (
                instagram.get("fecha_obtencion")
                if instagram else None
            ),
        },
    }

    # 7. Conservar los datos utilizados para generar
    # el reporte y permitir su trazabilidad.
    datos_utilizados = {
        "press_kit": press_kit,
        "demos": demos,
        "spotify": spotify,
        "lastfm": lastfm,
        "instagram": instagram,
        "verificacion_lastfm": {
            "perfil_encontrado": perfil_lastfm_encontrado,
            "identidad_confirmada": identidad_confirmada,
        },
    }

    return {
        "postulacion_id": postulacion_id,
        "viabilidad": viabilidad,
        "fuentes": fuentes,
        "datos_utilizados": datos_utilizados,
    }
