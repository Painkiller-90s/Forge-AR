from datetime import datetime, timezone


def postulacion_document(data: dict, sello_id: str) -> dict:
    ahora = datetime.now(timezone.utc)

    return {
        "sello_id": sello_id,

        "press_kit": {
            "nombre_artistico": data["nombre_artistico"],
            "correo_contacto": str(data["correo_contacto"]),
            "pais": data["pais"],
            "ciudad": data.get("ciudad"),
            "tipo_proyecto": data["tipo_proyecto"],
            "generos": data["generos"],
            "integrantes": data.get("integrantes", []),
            "biografia": data["biografia"],
            "anio_inicio": data.get("anio_inicio"),
            "spotify_url": data.get("spotify_url"),
            "instagram_url": data.get("instagram_url"),
            "mensaje_sello": data.get("mensaje_sello"),
        },

        "demo": {
            "nombre": data["nombre_demo"],
            "archivo_id": None,
        },

        "consentimientos": {
            "tratamiento_datos": data["consentimiento_datos"],
            "evaluacion_demo": data["autorizacion_demo"],
            "aceptados_en": ahora,
        },

        "estado": "recibida",

        "created_at": ahora,
        "updated_at": ahora,
    }