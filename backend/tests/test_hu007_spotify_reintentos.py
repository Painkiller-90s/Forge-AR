
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from app.services.spotify_retry_service import (
    solicitar_spotify_con_reintentos,
)


URL = "https://api.spotify.com/v1/artists/artista-prueba"


def crear_respuesta(estado, headers=None, datos=None):
    return httpx.Response(
        status_code=estado,
        headers=headers or {},
        json=datos or {"error": {"reason": "TEMPORARY"}},
        request=httpx.Request("GET", URL),
    )


class TestHU007SpotifyReintentos(
    unittest.IsolatedAsyncioTestCase
):

    def setUp(self):
        self.cliente = SimpleNamespace(
            request=AsyncMock()
        )

        # Evitar esperas reales durante las pruebas.
        parche = patch(
            "app.services.spotify_retry_service.asyncio.sleep",
            new_callable=AsyncMock,
        )
        self.sleep = parche.start()
        self.addCleanup(parche.stop)

    async def test_respuesta_exitosa(self):
        self.cliente.request.return_value = (
            crear_respuesta(200)
        )

        respuesta = await solicitar_spotify_con_reintentos(
            self.cliente, "GET", URL
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            self.cliente.request.await_count, 1
        )
        self.sleep.assert_not_awaited()

    async def test_error_503_tres_intentos(self):
        self.cliente.request.side_effect = [
            crear_respuesta(503),
            crear_respuesta(503),
            crear_respuesta(200),
        ]

        respuesta = await solicitar_spotify_con_reintentos(
            self.cliente, "GET", URL
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            self.cliente.request.await_count, 3
        )
        self.assertEqual(self.sleep.await_count, 2)

    async def test_error_400_sin_reintentos(self):
        self.cliente.request.return_value = (
            crear_respuesta(400)
        )

        respuesta = await solicitar_spotify_con_reintentos(
            self.cliente, "GET", URL
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            self.cliente.request.await_count, 1
        )
        self.sleep.assert_not_awaited()

    async def test_error_429_espera_breve(self):
        self.cliente.request.side_effect = [
            crear_respuesta(
                429,
                headers={"Retry-After": "1"},
            ),
            crear_respuesta(200),
        ]

        respuesta = await solicitar_spotify_con_reintentos(
            self.cliente, "GET", URL
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            self.cliente.request.await_count, 2
        )
        self.sleep.assert_awaited_once_with(1.0)

    async def test_error_429_espera_larga(self):
        self.cliente.request.return_value = (
            crear_respuesta(
                429,
                headers={"Retry-After": "30"},
            )
        )

        respuesta = await solicitar_spotify_con_reintentos(
            self.cliente, "GET", URL
        )

        self.assertEqual(respuesta.status_code, 429)
        self.assertEqual(
            self.cliente.request.await_count, 1
        )
        self.sleep.assert_not_awaited()

    async def test_cuota_agotada(self):
        self.cliente.request.return_value = (
            crear_respuesta(
                429,
                datos={
                    "error": {
                        "reason": "QUOTA_EXCEEDED"
                    }
                },
            )
        )

        respuesta = await solicitar_spotify_con_reintentos(
            self.cliente, "GET", URL
        )

        self.assertEqual(respuesta.status_code, 429)
        self.assertEqual(
            self.cliente.request.await_count, 1
        )
        self.sleep.assert_not_awaited()

    async def test_error_conexion_tres_intentos(self):
        error = httpx.ConnectError(
            "Error de conexion simulado",
            request=httpx.Request("GET", URL),
        )

        self.cliente.request.side_effect = [
            error,
            error,
            error,
        ]

        with self.assertRaises(httpx.ConnectError):
            await solicitar_spotify_con_reintentos(
                self.cliente, "GET", URL
            )

        self.assertEqual(
            self.cliente.request.await_count, 3
        )
        self.assertEqual(self.sleep.await_count, 2)


if __name__ == "__main__":
    unittest.main()
