
import unittest

from app.services.viability_service import (
    calcular_q_audio_postulacion,
    calcular_q_streaming,
    calcular_q_rrss,
    calcular_q_presskit,
    calcular_q_consistencia,
    calcular_score_viabilidad,
)


SPOTIFY_ID = "1234567890123456789012"
FECHA = "2026-11-12T15:00:00+00:00"


def crear_datos():
    postulacion = {
        "press_kit": {
            "nombre_artistico": "Mi Banda",
            "correo_contacto": "banda@ejemplo.cl",
            "pais": "Chile",
            "ciudad": "Santiago",
            "tipo_proyecto": "Banda",
            "generos": ["Thrash Metal"],
            "biografia": "X" * 350,
            "anio_inicio": 2018,
            "mensaje_sello": "Queremos presentar nuestra música.",
            "spotify_url": (
                f"https://open.spotify.com/artist/{SPOTIFY_ID}"
            ),
            "instagram_url": (
                "https://www.instagram.com/mi.banda/"
            ),
        },
        "demos": [
            {
                "archivo_id": "demo123",
                "sha256": "a" * 64,
                "audio_tecnico": {
                    "codec": "mp3",
                    "sample_rate_hz": 44100,
                },
                "validacion_tecnica": {
                    "valido": True,
                    "motivos_rechazo": [],
                    "q_audio": 80,
                },
            }
        ],
    }

    spotify = {
        "perfil": {
            "spotify_id": SPOTIFY_ID,
            "nombre": "Mi Banda",
        },
        "fuente": "Spotify Web API",
        "fecha_obtencion": FECHA,
        "estado_metricas": "actualizadas",
    }

    lastfm = {
        "estado": "verificada",
        "identidad_confirmada": True,
        "perfil_encontrado": True,
        "lastfm": {
            "oyentes_acumulados": 800,
            "reproducciones_acumuladas": 16000,
            "mbid": "mbid-ejemplo",
            "fuente": "Last.fm API",
            "fecha_obtencion": FECHA,
        },
    }

    instagram = {
        "estado_identidad": "pendiente_verificacion",
        "instagram": {
            "username": "mi.banda",
            "seguidores": 2000,
            "publicaciones_totales": 3,
            "publicaciones": [
                {
                    "likes": 80,
                    "comentarios": 20,
                    "es_propia": True,
                },
                {
                    "likes": 100,
                    "comentarios": 0,
                    "es_propia": True,
                },
                {
                    "likes": 60,
                    "comentarios": 20,
                    "es_propia": True,
                },
            ],
            "fuente": "Apify Instagram Profile Scraper",
            "fecha_obtencion": FECHA,
            "estado_metricas": "actualizadas",
        },
    }

    return postulacion, spotify, lastfm, instagram


class TestHU008IntegracionDatos(unittest.TestCase):

    def test_cinco_dimensiones_y_score(self):
        postulacion, spotify, lastfm, instagram = crear_datos()

        audio = calcular_q_audio_postulacion(
            postulacion["demos"]
        )

        streaming = calcular_q_streaming(
            metricas=lastfm["lastfm"],
            identidad_confirmada=lastfm["identidad_confirmada"],
            perfil_encontrado=lastfm["perfil_encontrado"],
        )

        rrss = calcular_q_rrss(instagram["instagram"])

        presskit = calcular_q_presskit(
            postulacion["press_kit"]
        )

        consistencia = calcular_q_consistencia(
            postulacion,
            spotify,
            lastfm,
            instagram,
        )

        resultado = calcular_score_viabilidad(
            q_audio=audio,
            q_streaming=streaming,
            q_rrss=rrss,
            q_presskit=presskit,
            q_consistencia=consistencia,
        )

        self.assertEqual(audio, 80)
        self.assertEqual(streaming["q_streaming"], 70)
        self.assertEqual(rrss["q_rrss"], 80)
        self.assertEqual(presskit["q_presskit"], 100)
        self.assertEqual(consistencia["q_consistencia"], 100)

        self.assertEqual(resultado["score"], 81)
        self.assertEqual(resultado["nivel_riesgo"], "bajo")

    def test_identidad_pendiente_no_genera_score(self):
        postulacion, spotify, lastfm, instagram = crear_datos()

        lastfm["identidad_confirmada"] = False
        lastfm["estado"] = "pendiente_verificacion"

        streaming = calcular_q_streaming(
            metricas=lastfm["lastfm"],
            identidad_confirmada=False,
            perfil_encontrado=True,
        )

        consistencia = calcular_q_consistencia(
            postulacion,
            spotify,
            lastfm,
            instagram,
        )

        resultado = calcular_score_viabilidad(
            q_audio=80,
            q_streaming=streaming,
            q_rrss=calcular_q_rrss(instagram["instagram"]),
            q_presskit=calcular_q_presskit(
                postulacion["press_kit"]
            ),
            q_consistencia=consistencia,
        )

        self.assertEqual(resultado["estado"], "no_evaluable")
        self.assertIsNone(resultado["score"])


if __name__ == "__main__":
    unittest.main()
