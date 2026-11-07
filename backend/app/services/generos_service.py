import unicodedata

from app.config.database import database


# Equivalencias definidas internamente.
# Las claves deben estar normalizadas.
# No agregar alias automáticamente.
ALIAS_GENEROS: dict[str, str] = {}


def _limpiar_etiqueta(etiqueta: str) -> str:
    if not isinstance(etiqueta, str):
        raise ValueError("Cada género debe ser texto.")

    texto = unicodedata.normalize("NFKC", etiqueta)
    texto = " ".join(texto.split())

    if not texto:
        raise ValueError("Las etiquetas de género no pueden estar vacías.")

    return texto


def _clave_genero(etiqueta: str) -> str:
    return _limpiar_etiqueta(etiqueta).casefold()


def _resolver_alias(etiqueta: str) -> str:
    texto = _limpiar_etiqueta(etiqueta)

    equivalente = ALIAS_GENEROS.get(_clave_genero(texto))

    if equivalente:
        return _limpiar_etiqueta(equivalente)

    return texto


async def obtener_generos_sello(sello_id: str) -> list[str]:
    """
    Recupera las etiquetas utilizadas en las postulaciones
    de un sello y elimina equivalencias duplicadas.
    """

    generos_existentes = await database.postulaciones.distinct(
        "press_kit.generos",
        {"sello_id": sello_id},
    )

    catalogo = {}

    for genero in generos_existentes:
        if not isinstance(genero, str):
            continue

        try:
            etiqueta = _resolver_alias(genero)
        except ValueError:
            continue

        clave = _clave_genero(etiqueta)

        catalogo.setdefault(clave, etiqueta)

    return sorted(
        catalogo.values(),
        key=_clave_genero,
    )


async def normalizar_generos_sello(
    generos: list[str],
    sello_id: str,
) -> list[str]:
    """
    Normaliza los géneros de una postulación.

    Reutiliza etiquetas existentes del sello,
    evita duplicados y permite incorporar etiquetas nuevas.
    """

    existentes = await obtener_generos_sello(sello_id)

    catalogo = {
        _clave_genero(genero): genero
        for genero in existentes
    }

    resultado = []
    etiquetas_procesadas = set()

    for genero in generos:
        etiqueta = _resolver_alias(genero)
        clave = _clave_genero(etiqueta)

        # Reutilizar una etiqueta existente si corresponde.
        etiqueta_canonica = catalogo.get(clave)

        # Incorporar una etiqueta nueva si no existe.
        if etiqueta_canonica is None:
            etiqueta_canonica = etiqueta
            catalogo[clave] = etiqueta_canonica

        # Evitar duplicados en la misma postulación.
        if clave not in etiquetas_procesadas:
            resultado.append(etiqueta_canonica)
            etiquetas_procesadas.add(clave)

    return resultado