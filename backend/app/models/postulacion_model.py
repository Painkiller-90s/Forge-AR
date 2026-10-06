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

        "demos": [
            {
                "nombre": demo["nombre"],
                "archivo_id": demo["archivo_id"],
                "nombre_archivo": demo["nombre_archivo"],
                "formato": demo["formato"],
                "tamano_bytes": demo["tamano_bytes"],
                "mime_type": demo.get("mime_type"),
                "sha256": demo["sha256"],
                "storage_key": demo["storage_key"],
                "uploaded_at": demo["uploaded_at"],

                # HU003 - Validación técnica del audio
                "audio_tecnico": {
                    "codec": demo["audio_tecnico"]["codec"],
                    "formato_contenedor": (
                        demo["audio_tecnico"]["formato_contenedor"]
                    ),
                    "sample_rate_hz": (
                        demo["audio_tecnico"]["sample_rate_hz"]
                    ),
                    "bitrate_bps": (
                        demo["audio_tecnico"]["bitrate_bps"]
                    ),
                    "bits_per_sample": (
                        demo["audio_tecnico"]["bits_per_sample"]
                    ),
                    "channels": (
                        demo["audio_tecnico"]["channels"]
                    ),
                    "duracion_segundos": (
                        demo["audio_tecnico"]["duracion_segundos"]
                    ),
                },

                "validacion_tecnica": {
                    "valido": demo["audio_tecnico"]["valido"],
                    "motivos_rechazo": (
                        demo["audio_tecnico"]["motivos_rechazo"]
                    ),
                    "q_audio": demo["audio_tecnico"]["q_audio"],
                },
            }
            for demo in data["demos"]
        ],

        "consentimientos": {
            "tratamiento_datos": data["consentimiento_datos"],
            "evaluacion_demo": data["autorizacion_demo"],
            "aceptados_en": ahora,
        },

        "estado": "recibida",

        "created_at": ahora,
        "updated_at": ahora,
    }