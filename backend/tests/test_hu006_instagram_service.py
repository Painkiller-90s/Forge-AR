import unittest

from app.services.instagram_service import (
    extraer_usuario_instagram,
    normalizar_perfil_instagram,
)


class TestInstagramService(unittest.TestCase):

    def test_url_instagram_valida(self):
        usuario = extraer_usuario_instagram(
            "https://www.instagram.com/scarcity.noise/"
        )

        self.assertEqual(usuario, "scarcity.noise")

    def test_url_instagram_invalida(self):
        with self.assertRaises(ValueError):
            extraer_usuario_instagram(
                "https://sitio-falso.com/artista"
            )

    def test_normalizacion_metricas(self):
        perfil = {
            "id": "12345",
            "username": "scarcity.noise",
            "followersCount": 2903,
            "postsCount": 67,
            "private": False,
            "latestPosts": [
                {
                    "id": "publicacion_1",
                    "likesCount": 148,
                    "commentsCount": 5,
                    "ownerUsername": "scarcity.noise",
                },
                {
                    "id": "publicacion_2",
                    "likesCount": 195,
                    "commentsCount": 20,
                    "ownerUsername": "otra.cuenta",
                },
                {
                    "id": "publicacion_3",
                    "likesCount": None,
                    "commentsCount": 2,
                    "ownerUsername": "scarcity.noise",
                },
            ],
        }

        metricas = normalizar_perfil_instagram(perfil)

        self.assertEqual(metricas["seguidores"], 2903)
        self.assertEqual(metricas["publicaciones_totales"], 67)
        self.assertEqual(metricas["publicaciones_recuperadas"], 2)

        self.assertTrue(metricas["publicaciones"][0]["es_propia"])
        self.assertFalse(metricas["publicaciones"][1]["es_propia"])

    def test_perfil_privado(self):
        perfil = {
            "username": "artista_privado",
            "followersCount": 100,
            "private": True,
        }

        with self.assertRaises(ValueError):
            normalizar_perfil_instagram(perfil)


if __name__ == "__main__":
    unittest.main()
