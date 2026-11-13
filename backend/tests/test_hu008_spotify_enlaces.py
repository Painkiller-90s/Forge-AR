
import unittest

from app.services.spotify_service import (
    extraer_id_artista_spotify,
)

from app.services.viability_service import (
    calcular_q_consistencia,
)

from tests.test_hu008_integracion_datos import (
    crear_datos,
    SPOTIFY_ID,
)


class TestEnlacesSpotify(unittest.TestCase):

    def test_enlace_normal(self):
        url = (
            f"https://open.spotify.com/artist/{SPOTIFY_ID}"
        )

        self.assertEqual(
            extraer_id_artista_spotify(url),
            SPOTIFY_ID,
        )

    def test_enlace_regional(self):
        url = (
            f"https://open.spotify.com/intl-es/artist/{SPOTIFY_ID}"
        )

        self.assertEqual(
            extraer_id_artista_spotify(url),
            SPOTIFY_ID,
        )

    def test_enlace_regional_con_parametros(self):
        url = (
            f"https://open.spotify.com/intl-es/artist/"
            f"{SPOTIFY_ID}?si=abc123"
        )

        self.assertEqual(
            extraer_id_artista_spotify(url),
            SPOTIFY_ID,
        )

    def test_rechazar_enlace_que_no_es_artista(self):
        url = (
            f"https://open.spotify.com/intl-es/playlist/"
            f"{SPOTIFY_ID}"
        )

        with self.assertRaises(ValueError):
            extraer_id_artista_spotify(url)

    def test_consistencia_admite_enlace_regional(self):
        postulacion, spotify, lastfm, instagram = crear_datos()

        postulacion["press_kit"]["spotify_url"] = (
            f"https://open.spotify.com/intl-es/artist/"
            f"{SPOTIFY_ID}?si=abc123"
        )

        resultado = calcular_q_consistencia(
            postulacion,
            spotify,
            lastfm,
            instagram,
        )

        self.assertEqual(
            resultado["desglose"]["spotify_enlace"],
            20,
        )
        self.assertEqual(
            resultado["q_consistencia"],
            100,
        )


if __name__ == "__main__":
    unittest.main()
