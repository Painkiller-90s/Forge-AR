from datetime import datetime, timezone
from urllib.parse import urlparse
from app.services.spotify_service import extraer_id_artista_spotify

def calcular_q_audio_postulacion(demos: list[dict]) -> int | None:
    """
    Consolida los puntajes técnicos de las demos
    utilizando la regla de capacidad demostrada.

    Se selecciona el mayor Q_audio entre las
    demos técnicamente válidas.

    Retorna None si no existen demos evaluables.
    """

    if not isinstance(demos, list):
        raise TypeError("Las demos deben entregarse como una lista.")

    puntajes = []

    for demo in demos:
        validacion = demo.get("validacion_tecnica") or {}

        if validacion.get("valido") is not True:
            continue

        puntaje = validacion.get("q_audio")

        if (
            isinstance(puntaje, bool)
            or not isinstance(puntaje, int)
            or not 0 <= puntaje <= 100
        ):
            raise ValueError(
                "El Q_audio de una demo válida debe ser "
                "un entero entre 0 y 100."
            )

        puntajes.append(puntaje)

    if not puntajes:
        return None

    return max(puntajes)


def _validar_metrica_lastfm(valor: int, campo: str) -> int:
    """Valida que una métrica de Last.fm sea un entero no negativo."""

    if (
        isinstance(valor, bool)
        or not isinstance(valor, int)
        or valor < 0
    ):
        raise ValueError(
            f"{campo} debe ser un entero no negativo."
        )

    return valor


def calcular_puntaje_audiencia(oyentes: int) -> int:
    """
    Calcula hasta 50 puntos según los oyentes acumulados.
    """

    oyentes = _validar_metrica_lastfm(
        oyentes,
        "Los oyentes acumulados",
    )

    if oyentes >= 10000:
        return 50
    elif oyentes >= 5000:
        return 40
    elif oyentes >= 1000:
        return 30
    elif oyentes >= 250:
        return 20
    elif oyentes >= 1:
        return 10

    return 0


def calcular_puntaje_fidelidad(
    oyentes: int,
    reproducciones: int,
) -> int:
    """
    Calcula hasta 50 puntos según el ratio
    de reproducciones por oyente.
    """

    oyentes = _validar_metrica_lastfm(
        oyentes,
        "Los oyentes acumulados",
    )

    reproducciones = _validar_metrica_lastfm(
        reproducciones,
        "Las reproducciones acumuladas",
    )

    # Sin oyentes no existe una relación evaluable.
    if oyentes == 0:
        return 0

    ratio = reproducciones / oyentes

    if ratio >= 15:
        return 50
    elif ratio >= 10:
        return 40
    elif ratio >= 5:
        return 30
    elif ratio >= 2:
        return 20

    return 10



def calcular_q_streaming(
    metricas: dict | None,
    identidad_confirmada: bool,
    perfil_encontrado: bool = True,
) -> dict | None:
    """
    Calcula Q_streaming utilizando métricas de Last.fm.

    Distribución:
        - Audiencia: 50 puntos.
        - Fidelidad: 50 puntos.

    Retorna None si la identidad no está confirmada.
    Si Last.fm no encuentra el perfil, retorna 0 puntos.
    """

    # Un perfil inexistente recibe cero según la rúbrica.
    if perfil_encontrado is False:
        return {
            "q_streaming": 0,
            "puntaje_audiencia": 0,
            "puntaje_fidelidad": 0,
            "ratio_reproducciones_oyente": 0.0,
        }

    if identidad_confirmada is not True:
        return None

    if not isinstance(metricas, dict):
        raise TypeError(
            "Las métricas de Last.fm deben entregarse como un diccionario."
        )

    oyentes = _validar_metrica_lastfm(
        metricas.get("oyentes_acumulados"),
        "Los oyentes acumulados",
    )

    reproducciones = _validar_metrica_lastfm(
        metricas.get("reproducciones_acumuladas"),
        "Las reproducciones acumuladas",
    )

    puntaje_audiencia = calcular_puntaje_audiencia(oyentes)

    puntaje_fidelidad = calcular_puntaje_fidelidad(
        oyentes,
        reproducciones,
    )

    ratio = (
        reproducciones / oyentes
        if oyentes > 0
        else 0.0
    )

    return {
        "q_streaming": puntaje_audiencia + puntaje_fidelidad,
        "puntaje_audiencia": puntaje_audiencia,
        "puntaje_fidelidad": puntaje_fidelidad,
        "ratio_reproducciones_oyente": round(ratio, 2),
    }


def _puntuar_tasa_rrss(tasa: float, umbrales: tuple) -> int:
    """Convierte una tasa porcentual en un puntaje de 0 a 50."""

    for minimo, puntos in umbrales:
        if tasa >= minimo:
            return puntos

    return 10 if tasa > 0 else 0


def calcular_q_rrss(metricas: dict | None) -> dict | None:
    """
    Calcula Q_rrss usando las publicaciones propias de Instagram.

    Distribución:
        - Tasa de likes promedio: 50 puntos.
        - Tasa de comentarios promedio: 50 puntos.

    Retorna None cuando no existen datos suficientes.
    """

    if metricas is None:
        return None

    if not isinstance(metricas, dict):
        raise TypeError(
            "Las métricas de Instagram deben ser un diccionario."
        )

    seguidores = metricas.get("seguidores")

    if (
        isinstance(seguidores, bool)
        or not isinstance(seguidores, int)
        or seguidores < 0
    ):
        raise ValueError(
            "Los seguidores deben ser un entero no negativo."
        )

    # Sin seguidores no podemos normalizar los promedios.
    if seguidores == 0:
        return None

    publicaciones = metricas.get("publicaciones")

    if not isinstance(publicaciones, list):
        return None

    publicaciones_validas = []

    for publicacion in publicaciones:
        if not isinstance(publicacion, dict):
            continue

        # Solo publicaciones identificadas como propias.
        if publicacion.get("es_propia") is not True:
            continue

        likes = publicacion.get("likes")
        comentarios = publicacion.get("comentarios")

        # Excluir publicaciones con métricas inválidas.
        if (
            isinstance(likes, bool)
            or isinstance(comentarios, bool)
            or not isinstance(likes, int)
            or not isinstance(comentarios, int)
            or likes < 0
            or comentarios < 0
        ):
            continue

        publicaciones_validas.append(publicacion)

    cantidad = len(publicaciones_validas)

    if cantidad == 0:
        # Un perfil confirmado sin publicaciones recibe 0.
        total = metricas.get("publicaciones_totales")

        if isinstance(total, bool) or total != 0:
            return None

        likes_promedio = 0.0
        comentarios_promedio = 0.0

    else:
        likes_promedio = (
            sum(p["likes"] for p in publicaciones_validas)
            / cantidad
        )

        comentarios_promedio = (
            sum(p["comentarios"] for p in publicaciones_validas)
            / cantidad
        )

    tasa_likes = (likes_promedio / seguidores) * 100
    tasa_comentarios = (
        comentarios_promedio / seguidores
    ) * 100

    # Rúbrica de likes: máximo 50 puntos.
    puntaje_likes = _puntuar_tasa_rrss(
        tasa_likes,
        (
            (6.0, 50),
            (4.0, 40),
            (2.0, 30),
            (1.0, 20),
        ),
    )

    # Rúbrica de comentarios: máximo 50 puntos.
    puntaje_comentarios = _puntuar_tasa_rrss(
        tasa_comentarios,
        (
            (1.0, 50),
            (0.5, 40),
            (0.25, 30),
            (0.1, 20),
        ),
    )

    return {
        "q_rrss": puntaje_likes + puntaje_comentarios,
        "puntaje_likes": puntaje_likes,
        "puntaje_comentarios": puntaje_comentarios,
        "likes_promedio": round(likes_promedio, 2),
        "comentarios_promedio": round(
            comentarios_promedio, 2
        ),
        "tasa_likes_pct": round(tasa_likes, 2),
        "tasa_comentarios_pct": round(
            tasa_comentarios, 2
        ),
        "seguidores": seguidores,
        "publicaciones_evaluadas": cantidad,
        "fuente": metricas.get("fuente"),
        "fecha_obtencion": metricas.get("fecha_obtencion"),
        "estado_metricas": metricas.get("estado_metricas"),
    }



def _texto_presskit_presente(
    valor: object,
    minimo: int = 1,
) -> bool:
    """Comprueba si un campo contiene texto suficiente."""
    return (
        isinstance(valor, str)
        and len(valor.strip()) >= minimo
    )


def calcular_q_presskit(press_kit: dict | None) -> dict:
    """
    Evalúa la completitud del Press Kit.

    Ponderación interna:
        - Campos obligatorios: 60 puntos.
        - Ciudad: 5 puntos.
        - Año de inicio: 5 puntos.
        - Mensaje al sello: 15 puntos.
        - Extensión de biografía: hasta 15 puntos.

    No evalúa la calidad artística del contenido.
    """

    if press_kit is None:
        press_kit = {}

    if not isinstance(press_kit, dict):
        raise TypeError(
            "El Press Kit debe ser un diccionario."
        )

    # Comprobar los seis campos obligatorios.
    campos_requeridos = {
        "nombre_artistico": _texto_presskit_presente(
            press_kit.get("nombre_artistico"), 2
        ),
        "correo_contacto": _texto_presskit_presente(
            press_kit.get("correo_contacto")
        ),
        "pais": _texto_presskit_presente(
            press_kit.get("pais"), 2
        ),
        "tipo_proyecto": _texto_presskit_presente(
            press_kit.get("tipo_proyecto"), 2
        ),
        "generos": (
            isinstance(press_kit.get("generos"), list)
            and 1 <= len(press_kit["generos"]) <= 10
            and all(
                _texto_presskit_presente(g)
                for g in press_kit["generos"]
            )
        ),
        "biografia": _texto_presskit_presente(
            press_kit.get("biografia"), 10
        ),
    }

    faltantes = [
        campo
        for campo, presente in campos_requeridos.items()
        if not presente
    ]

    # No generar un puntaje definitivo si faltan
    # datos obligatorios.
    if faltantes:
        return {
            "estado": "no_evaluable",
            "q_presskit": None,
            "campos_obligatorios_faltantes": faltantes,
        }

    # Bono por extensión de la biografía.
    biografia = press_kit["biografia"].strip()
    caracteres = len(biografia)

    if caracteres >= 350:
        bono = 15
    elif caracteres >= 150:
        bono = 7
    else:
        bono = 0

    # El año de inicio debe ser un año plausible.
    anio = press_kit.get("anio_inicio")

    anio_valido = (
        isinstance(anio, int)
        and not isinstance(anio, bool)
        and 1900 <= anio <= datetime.now(timezone.utc).year
    )

    # Desglose para explicar el puntaje al evaluador.
    desglose = {
        **{
            campo: 10
            for campo in campos_requeridos
        },
        "ciudad": (
            5
            if _texto_presskit_presente(
                press_kit.get("ciudad")
            )
            else 0
        ),
        "anio_inicio": 5 if anio_valido else 0,
        "mensaje_sello": (
            15
            if _texto_presskit_presente(
                press_kit.get("mensaje_sello")
            )
            else 0
        ),
        "bono_biografia": bono,
    }

    return {
        "estado": "evaluable",
        "q_presskit": sum(desglose.values()),
        "desglose": desglose,
        "caracteres_biografia": caracteres,
        "campos_obligatorios_faltantes": [],
    }



def _spotify_id_en_url(url: object) -> str | None:
    """
    Obtiene el ID de Spotify reutilizando el extractor oficial
    del proyecto. Devuelve None si el enlace es inválido.
    """

    if not isinstance(url, str):
        return None

    try:
        return extraer_id_artista_spotify(url)
    except ValueError:
        return None



def _usuario_en_url_instagram(url: object) -> str | None:
    """Extrae el usuario declarado en Instagram."""
    if not isinstance(url, str):
        return None

    enlace = urlparse(url.strip())
    partes = [p for p in enlace.path.split("/") if p]

    if (
        enlace.scheme not in {"http", "https"}
        or enlace.hostname not in {
            "instagram.com",
            "www.instagram.com",
            "m.instagram.com",
        }
        or len(partes) != 1
    ):
        return None

    return partes[0].casefold()


def _fuente_fecha_validas(datos: dict) -> bool:
    """Comprueba la trazabilidad básica de una consulta externa."""
    fuente = datos.get("fuente")
    fecha = datos.get("fecha_obtencion")

    if not isinstance(fuente, str) or not fuente.strip():
        return False

    if not isinstance(fecha, str):
        return False

    try:
        valor = datetime.fromisoformat(
            fecha.replace("Z", "+00:00")
        )
    except ValueError:
        return False

    return valor.tzinfo is not None


def _demo_trazable(demo: object) -> bool:
    """Comprueba metadatos y registro de validación técnica."""
    if not isinstance(demo, dict):
        return False

    audio = demo.get("audio_tecnico")
    validacion = demo.get("validacion_tecnica")

    return (
        isinstance(demo.get("archivo_id"), str)
        and bool(demo["archivo_id"].strip())
        and isinstance(demo.get("sha256"), str)
        and bool(demo["sha256"].strip())
        and isinstance(audio, dict)
        and isinstance(audio.get("codec"), str)
        and bool(audio["codec"].strip())
        and isinstance(audio.get("sample_rate_hz"), int)
        and not isinstance(audio["sample_rate_hz"], bool)
        and audio["sample_rate_hz"] > 0
        and isinstance(validacion, dict)
        and type(validacion.get("valido")) is bool
        and isinstance(validacion.get("motivos_rechazo"), list)
        and isinstance(validacion.get("q_audio"), int)
        and not isinstance(validacion["q_audio"], bool)
        and 0 <= validacion["q_audio"] <= 100
    )


def calcular_q_consistencia(
    postulacion: dict,
    respuesta_spotify: dict | None,
    respuesta_lastfm: dict | None,
    respuesta_instagram: dict | None,
) -> dict:
    """
    Calcula Q_consistencia con información ya obtenida.

    No realiza consultas externas.

    Ponderación:
        Spotify: 20 puntos.
        MusicBrainz: 25 puntos.
        Instagram: 20 puntos.
        Trazabilidad de fuentes: 20 puntos.
        Metadatos de demos: 15 puntos.

    No asigna cero cuando falta una verificación.
    """

    if not isinstance(postulacion, dict):
        raise TypeError(
            "La postulación debe ser un diccionario."
        )

    for nombre, respuesta in (
        ("Spotify", respuesta_spotify),
        ("Last.fm", respuesta_lastfm),
        ("Instagram", respuesta_instagram),
    ):
        if respuesta is not None and not isinstance(
            respuesta, dict
        ):
            raise TypeError(
                f"La respuesta de {nombre} debe ser "
                "un diccionario o None."
            )

    press_kit = postulacion.get("press_kit") or {}

    if not isinstance(press_kit, dict):
        raise TypeError(
            "El Press Kit debe ser un diccionario."
        )

    desglose = {}
    faltantes = []

    # 1. Coincidencia del ID real obtenido desde Spotify.
    esperado = _spotify_id_en_url(
        press_kit.get("spotify_url")
    )

    perfil_spotify = (
        respuesta_spotify.get("perfil")
        if respuesta_spotify is not None
        else None
    )

    obtenido = (
        perfil_spotify.get("spotify_id")
        if isinstance(perfil_spotify, dict)
        else None
    )

    if esperado is None or obtenido is None:
        desglose["spotify_enlace"] = None
        faltantes.append("spotify_enlace")
    else:
        desglose["spotify_enlace"] = (
            20 if esperado == obtenido else 0
        )

    # 2. Verificación de identidad mediante MusicBrainz.
    estado_identidad = (
        respuesta_lastfm.get("estado")
        if respuesta_lastfm is not None
        else None
    )

    identidad_confirmada = (
        respuesta_lastfm.get("identidad_confirmada")
        if respuesta_lastfm is not None
        else None
    )

    if (
        estado_identidad == "verificada"
        and identidad_confirmada is True
    ):
        desglose["identidad_musicbrainz"] = 25
    else:
        desglose["identidad_musicbrainz"] = None
        faltantes.append("identidad_musicbrainz")

    # 3. Coincidencia del usuario declarado en Instagram.
    esperado_instagram = _usuario_en_url_instagram(
        press_kit.get("instagram_url")
    )

    perfil_instagram = (
        respuesta_instagram.get("instagram")
        if respuesta_instagram is not None
        else None
    )

    obtenido_instagram = (
        perfil_instagram.get("username")
        if isinstance(perfil_instagram, dict)
        else None
    )

    if (
        esperado_instagram is None
        or not isinstance(obtenido_instagram, str)
        or not obtenido_instagram
    ):
        desglose["instagram_enlace"] = None
        faltantes.append("instagram_enlace")
    else:
        desglose["instagram_enlace"] = (
            20
            if esperado_instagram == obtenido_instagram.casefold()
            else 0
        )

    # 4. Fuente y fecha de Spotify, Last.fm e Instagram.
    metricas_lastfm = (
        respuesta_lastfm.get("lastfm")
        if respuesta_lastfm is not None
        else None
    )

    if (
        not isinstance(respuesta_spotify, dict)
        or not isinstance(metricas_lastfm, dict)
        or not isinstance(perfil_instagram, dict)
    ):
        desglose["fuentes_fechas"] = None
        faltantes.append("fuentes_fechas")
    else:
        fuentes_validas = all(
            _fuente_fecha_validas(datos)
            for datos in (
                respuesta_spotify,
                metricas_lastfm,
                perfil_instagram,
            )
        )

        desglose["fuentes_fechas"] = (
            20 if fuentes_validas else 0
        )

    # 5. Trazabilidad de las demos almacenadas.
    demos = postulacion.get("demos")

    if not isinstance(demos, list) or not demos:
        desglose["demos_trazables"] = None
        faltantes.append("demos_trazables")
    else:
        desglose["demos_trazables"] = (
            15 if all(_demo_trazable(d) for d in demos) else 0
        )

    # Conservar qué fuentes utilizaron datos de respaldo.
    fuentes_desactualizadas = []

    if (
        isinstance(respuesta_spotify, dict)
        and respuesta_spotify.get("estado_metricas")
        == "desactualizadas"
    ):
        fuentes_desactualizadas.append("spotify")

    if (
        isinstance(perfil_instagram, dict)
        and perfil_instagram.get("estado_metricas")
        == "desactualizadas"
    ):
        fuentes_desactualizadas.append("instagram")

    evaluable = not faltantes

    return {
        "estado": (
            "evaluable" if evaluable else "no_evaluable"
        ),
        "q_consistencia": (
            sum(desglose.values()) if evaluable else None
        ),
        "desglose": desglose,
        "criterios_no_evaluables": faltantes,
        "fuentes_desactualizadas": fuentes_desactualizadas,
    }



PESOS_SCORE_VIABILIDAD = {
    "q_audio": 30,
    "q_streaming": 30,
    "q_rrss": 20,
    "q_presskit": 10,
    "q_consistencia": 10,
}


def calcular_score_viabilidad(
    *,
    q_audio: int | None,
    q_streaming: dict | None,
    q_rrss: dict | None,
    q_presskit: dict | None,
    q_consistencia: dict | None,
) -> dict:
    """
    Combina las cinco dimensiones de HU008.

    No asigna un Score definitivo si alguna
    dimensión carece de puntuación evaluable.
    """

    dimensiones = {
        "q_audio": q_audio,
        "q_streaming": q_streaming,
        "q_rrss": q_rrss,
        "q_presskit": q_presskit,
        "q_consistencia": q_consistencia,
    }

    puntajes = {}
    faltantes = []
    motivos = []

    for nombre, resultado in dimensiones.items():

        if nombre == "q_audio":
            puntaje = resultado

        elif resultado is None:
            puntaje = None

        elif isinstance(resultado, dict):
            puntaje = resultado.get(nombre)

        else:
            raise TypeError(
                f"{nombre} debe ser un diccionario o None."
            )

        if puntaje is None:
            faltantes.append(nombre)
            motivo = f"{nombre}: sin puntaje evaluable"

            if (
                nombre == "q_presskit"
                and isinstance(resultado, dict)
            ):
                campos = resultado.get(
                    "campos_obligatorios_faltantes"
                )

                if isinstance(campos, list) and campos:
                    motivo += (
                        "; campos obligatorios faltantes: "
                        + ", ".join(map(str, campos))
                    )

            elif (
                nombre == "q_consistencia"
                and isinstance(resultado, dict)
            ):
                criterios = resultado.get(
                    "criterios_no_evaluables"
                )

                if isinstance(criterios, list) and criterios:
                    motivo += (
                        "; criterios sin verificar: "
                        + ", ".join(map(str, criterios))
                    )

            motivos.append(motivo)
            continue

        # Se rechazan booleanos, valores fuera de rango
        # y puntuaciones que no sean enteros.
        if type(puntaje) is not int or not 0 <= puntaje <= 100:
            raise ValueError(
                f"{nombre} debe ser un entero entre 0 y 100."
            )

        puntajes[nombre] = puntaje

    # CA07 y CA08: no evaluable con motivos explícitos.
    if faltantes:
        return {
            "estado": "no_evaluable",
            "score": None,
            "nivel_riesgo": None,
            "dimensiones": dimensiones,
            "aportes": None,
            "dimensiones_faltantes": faltantes,
            "motivos_no_evaluable": motivos,
        }

    # Ponderación entera para evitar imprecisiones
    # en las comparaciones de límites de riesgo.
    total_centesimas = sum(
        puntajes[nombre] * peso
        for nombre, peso in PESOS_SCORE_VIABILIDAD.items()
    )

    aportes = {
        nombre: puntajes[nombre] * peso / 100
        for nombre, peso in PESOS_SCORE_VIABILIDAD.items()
    }

    score = total_centesimas / 100

    # CA09, CA10 y CA11: clasificación de riesgo.
    if total_centesimas <= 4000:
        nivel_riesgo = "alto"

    elif total_centesimas <= 7000:
        nivel_riesgo = "medio"

    else:
        nivel_riesgo = "bajo"

    return {
        "estado": "evaluable",
        "score": score,
        "nivel_riesgo": nivel_riesgo,
        "dimensiones": dimensiones,
        "aportes": aportes,
        "dimensiones_faltantes": [],
        "motivos_no_evaluable": [],
    }
