def serializar_datos_utilizados(datos: dict | None) -> dict:
    """
    Prepara los datos utilizados para una respuesta HTTP.

    Conserva la información de evaluación, pero elimina
    las claves internas de almacenamiento.
    """

    if not isinstance(datos, dict):
        return {}

    def sanitizar(valor):

        if isinstance(valor, dict):
            return {
                clave: sanitizar(contenido)
                for clave, contenido in valor.items()
                if clave != "storage_key"
            }

        if isinstance(valor, list):
            return [
                sanitizar(elemento)
                for elemento in valor
            ]

        return valor

    return sanitizar(datos)