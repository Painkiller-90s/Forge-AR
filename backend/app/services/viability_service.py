
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

