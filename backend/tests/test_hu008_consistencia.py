
import unittest

from app.services.viability_service import (
    calcular_q_consistencia,
)


SPOTIFY_ID = "0OdUWJ0sBjDrqHygGUXeCF"

POSTULACION = {
    "press_kit": {
        "spotify_url": (
            f"https://open.spotify.com/artist/{SPOTIFY_ID}"
        ),
        "instagram_url": (
            "https://www.instagram.com/mi.banda/"
        ),
    },
    "demos": [
        {
            "archivo_id": "archivo123",
            "sha256": "f" * 64,
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

SPOTIFY = {
    "perfil": {"spotify_id": SPOTIFY_ID},
    "fuente": "Spotify Web API",
    "fecha_obtencion": "2026-11-12T15:00:00Z",
    "estado_metricas": "actualizadas",
}

LASTFM = {
    "estado": "verificada",
    "identidad_confirmada": True,
    "lastfm": {
        "fuente": "Last.fm API",
        "fecha_obtencion": "2026-11-12T15:00:00Z",
    },
}

INSTAGRAM = {
    "instagram": {
        "username": "mi.banda",
        "fuente": "Apify Instagram Profile Scraper",
        "fecha_obtencion": "2026-11-12T15:00:00Z",
        "estado_metricas": "actualizadas",
    },
}


class TestQConsistencia(unittest.TestCase):

    def calcular(
        self,
        postulacion=POSTULACION,
        spotify=SPOTIFY,
        lastfm=LASTFM,
        instagram=INSTAGRAM,
    ):
        return calcular_q_consistencia(
            postulacion,
            spotify,
            lastfm,
            instagram,
        )

    def test_puntaje_maximo(self):
        resultado = self.calcular()

        self.assertEqual(resultado["estado"], "evaluable")
        self.assertEqual(resultado["q_consistencia"], 100)

    def test_spotify_no_coincide(self):
        datos = {
            **SPOTIFY,
            "perfil": {"spotify_id": "x" * 22},
        }

        resultado = self.calcular(spotify=datos)

        self.assertEqual(resultado["q_consistencia"], 80)
        self.assertEqual(
            resultado["desglose"]["spotify_enlace"],
            0,
        )

    def test_instagram_no_coincide(self):
        datos = {
            "instagram": {
                **INSTAGRAM["instagram"],
                "username": "otra.banda",
            }
        }

        resultado = self.calcular(instagram=datos)

        self.assertEqual(resultado["q_consistencia"], 80)

    def test_identidad_pendiente(self):
        datos = {
            **LASTFM,
            "estado": "pendiente_verificacion",
            "identidad_confirmada": False,
        }

        resultado = self.calcular(lastfm=datos)

        self.assertIsNone(resultado["q_consistencia"])
        self.assertIn(
            "identidad_musicbrainz",
            resultado["criterios_no_evaluables"],
        )

    def test_servicio_no_disponible(self):
        resultado = self.calcular(spotify=None)

        self.assertEqual(resultado["estado"], "no_evaluable")
        self.assertIsNone(resultado["q_consistencia"])

    def test_fuente_sin_trazabilidad(self):
        datos = {**SPOTIFY, "fuente": None}

        resultado = self.calcular(spotify=datos)

        self.assertEqual(resultado["q_consistencia"], 80)
        self.assertEqual(
            resultado["desglose"]["fuentes_fechas"],
            0,
        )

    def test_respaldo_no_descontar_puntos(self):
        datos = {
            **SPOTIFY,
            "estado_metricas": "desactualizadas",
        }

        resultado = self.calcular(spotify=datos)

        self.assertEqual(resultado["q_consistencia"], 100)
        self.assertIn(
            "spotify",
            resultado["fuentes_desactualizadas"],
        )

    def test_demo_sin_metadatos(self):
        datos = {
            **POSTULACION,
            "demos": [{"archivo_id": "archivo123"}],
        }

        resultado = self.calcular(postulacion=datos)

        self.assertEqual(resultado["q_consistencia"], 85)

    def test_sin_demos(self):
        datos = {**POSTULACION, "demos": []}

        resultado = self.calcular(postulacion=datos)

        self.assertIsNone(resultado["q_consistencia"])

    def test_resultado_determinista(self):
        self.assertEqual(
            self.calcular(),
            self.calcular(),
        )

    def test_rechazar_respuesta_invalida(self):
        with self.assertRaises(TypeError):
            self.calcular(spotify=[])


if __name__ == "__main__":
    unittest.main()
