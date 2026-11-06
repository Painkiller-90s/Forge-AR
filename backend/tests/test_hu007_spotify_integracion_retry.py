
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import spotify_service


SPOTIFY_ID = "1234567890123456789012"


class TestHU007SpotifyIntegracionRetry(
    unittest.IsolatedAsyncioTestCase
):

    def setUp(self):
        parche_cliente = patch.object(
            spotify_service.httpx,
            "AsyncClient",
        )
        cliente_mock = parche_cliente.start()
        self.addCleanup(parche_cliente.stop)

        self.cliente = (
            cliente_mock.return_value
            .__aenter__.return_value
        )

        parche_solicitud = patch.object(
            spotify_service,
            "solicitar_spotify_con_reintentos",
            new_callable=AsyncMock,
        )
        self.solicitar = parche_solicitud.start()
        self.addCleanup(parche_solicitud.stop)

    def simular_respuesta(self, datos):
        respuesta = MagicMock()
        respuesta.status_code = 200
        respuesta.json.return_value = datos
        self.solicitar.return_value = respuesta

    async def test_token_utiliza_reintentos(self):
        self.simular_respuesta({
            "access_token": "token-simulado"
        })

        with patch.dict(
            spotify_service.os.environ,
            {
                "SPOTIFY_CLIENT_ID": "id-prueba",
                "SPOTIFY_CLIENT_SECRET": "secreto-prueba",
            },
        ):
            token = await (
                spotify_service.obtener_token_spotify()
            )

        self.assertEqual(token, "token-simulado")

        self.solicitar.assert_awaited_once_with(
            self.cliente,
            "POST",
            "https://accounts.spotify.com/api/token",
            auth=("id-prueba", "secreto-prueba"),
            data={"grant_type": "client_credentials"},
        )

    async def test_busqueda_utiliza_reintentos(self):
        self.simular_respuesta({
            "artists": {
                "items": [{
                    "id": SPOTIFY_ID,
                    "name": "Artista prueba",
                    "external_urls": {
                        "spotify": (
                            "https://open.spotify.com/artist/"
                            + SPOTIFY_ID
                        )
                    },
                }]
            }
        })

        with patch.object(
            spotify_service,
            "obtener_token_spotify",
            new=AsyncMock(return_value="token-prueba"),
        ):
            artistas = await (
                spotify_service.buscar_artistas_spotify(
                    "Artista prueba"
                )
            )

        self.assertEqual(len(artistas), 1)
        self.assertEqual(
            artistas[0]["spotify_id"], SPOTIFY_ID
        )

        self.solicitar.assert_awaited_once_with(
            self.cliente,
            "GET",
            "https://api.spotify.com/v1/search",
            headers={
                "Authorization": "Bearer token-prueba"
            },
            params={
                "q": "Artista prueba",
                "type": "artist",
                "limit": 5,
            },
        )

    async def test_perfil_utiliza_reintentos(self):
        self.simular_respuesta({
            "id": SPOTIFY_ID,
            "name": "Artista prueba",
            "external_urls": {},
            "followers": {"total": 1500},
            "popularity": 35,
            "genres": ["rock"],
        })

        with patch.object(
            spotify_service,
            "obtener_token_spotify",
            new=AsyncMock(return_value="token-prueba"),
        ):
            perfil = await (
                spotify_service.consultar_artista_spotify(
                    SPOTIFY_ID
                )
            )

        self.assertEqual(perfil["seguidores"], 1500)

        self.solicitar.assert_awaited_once_with(
            self.cliente,
            "GET",
            (
                "https://api.spotify.com/v1/artists/"
                + SPOTIFY_ID
            ),
            headers={
                "Authorization": "Bearer token-prueba"
            },
        )

    async def test_catalogo_utiliza_reintentos(self):
        self.simular_respuesta({
            "total": 1,
            "items": [{
                "name": "Disco prueba",
                "album_type": "album",
                "release_date": "2026-01-01",
            }],
        })

        with patch.object(
            spotify_service,
            "obtener_token_spotify",
            new=AsyncMock(return_value="token-prueba"),
        ):
            catalogo = await (
                spotify_service.consultar_catalogo_spotify(
                    SPOTIFY_ID
                )
            )

        self.assertEqual(
            catalogo["total_lanzamientos"], 1
        )

        self.solicitar.assert_awaited_once_with(
            self.cliente,
            "GET",
            (
                "https://api.spotify.com/v1/artists/"
                + SPOTIFY_ID + "/albums"
            ),
            headers={
                "Authorization": "Bearer token-prueba"
            },
            params={
                "include_groups": "album,single",
                "market": "CL",
                "limit": 5,
            },
        )


if __name__ == "__main__":
    unittest.main()
