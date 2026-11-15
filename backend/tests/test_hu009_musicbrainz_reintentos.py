
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.services import artist_identity_service as service


def crear_respuesta(status, json_data=None, headers=None, content=None):

    request = httpx.Request(
        "GET",
        "https://musicbrainz.org/ws/2/artist/test-mbid"
    )

    if json_data is not None:
        return httpx.Response(
            status,
            json=json_data,
            headers=headers,
            request=request
        )

    return httpx.Response(
        status,
        content=content,
        headers=headers,
        request=request
    )


class TestMusicBrainzReintentos(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.cliente = object()

        self.solicitud_patch = patch.object(
            service,
            "_solicitar_musicbrainz",
            new_callable=AsyncMock
        )

        self.solicitud = self.solicitud_patch.start()

        self.sleep_patch = patch.object(
            service.asyncio,
            "sleep",
            new_callable=AsyncMock
        )

        self.sleep = self.sleep_patch.start()

    async def asyncTearDown(self):

        self.solicitud_patch.stop()
        self.sleep_patch.stop()

    async def test_reintentar_hasta_respuesta_200(self):

        self.solicitud.side_effect = [
            crear_respuesta(503),
            crear_respuesta(503),
            crear_respuesta(200, {"id": "test-mbid"})
        ]

        resultado = await service._consultar_datos_musicbrainz(
            self.cliente,
            "test-mbid"
        )

        self.assertEqual(resultado["id"], "test-mbid")
        self.assertEqual(self.solicitud.call_count, 3)

        esperas = [
            llamada.args[0]
            for llamada in self.sleep.await_args_list
        ]

        self.assertEqual(esperas, [1.0, 2.0])

    async def test_respetar_retry_after(self):

        self.solicitud.side_effect = [
            crear_respuesta(
                429,
                headers={"Retry-After": "7"}
            ),
            crear_respuesta(200, {"id": "test-mbid"})
        ]

        resultado = await service._consultar_datos_musicbrainz(
            self.cliente,
            "test-mbid"
        )

        self.assertEqual(resultado["id"], "test-mbid")

        self.sleep.assert_awaited_once_with(7.0)

    async def test_reintentar_timeout(self):

        self.solicitud.side_effect = [
            httpx.TimeoutException("Timeout de prueba"),
            crear_respuesta(200, {"id": "test-mbid"})
        ]

        resultado = await service._consultar_datos_musicbrainz(
            self.cliente,
            "test-mbid"
        )

        self.assertEqual(resultado["id"], "test-mbid")
        self.assertEqual(self.solicitud.call_count, 2)

    async def test_no_reintentar_http_404(self):

        self.solicitud.return_value = crear_respuesta(404)

        with self.assertRaises(httpx.HTTPStatusError):

            await service._consultar_datos_musicbrainz(
                self.cliente,
                "test-mbid"
            )

        self.assertEqual(self.solicitud.call_count, 1)

    async def test_reintentar_json_invalido(self):

        self.solicitud.side_effect = [
            crear_respuesta(200, content=b"respuesta invalida"),
            crear_respuesta(200, {"id": "test-mbid"})
        ]

        resultado = await service._consultar_datos_musicbrainz(
            self.cliente,
            "test-mbid"
        )

        self.assertEqual(resultado["id"], "test-mbid")
        self.assertEqual(self.solicitud.call_count, 2)


if __name__ == "__main__":
    unittest.main()
