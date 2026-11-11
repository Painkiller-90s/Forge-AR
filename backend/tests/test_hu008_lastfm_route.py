
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.routes import lastfm_route
from app.services.lastfm_service import ArtistaLastFMNoEncontrado


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"
SPOTIFY_ID = "1234567890123456789012"

POSTULACION = {
    "_id": ObjectId(POSTULACION_ID),
    "sello_id": "sello_01",
    "press_kit": {
        "spotify_url": (
            f"https://open.spotify.com/artist/{SPOTIFY_ID}"
        )
    },
}

SPOTIFY = {
    "nombre": "Neurosis",
    "url": f"https://open.spotify.com/artist/{SPOTIFY_ID}",
}

METRICAS = {
    "nombre": "Neurosis",
    "mbid": "mbid-prueba-123",
    "url": "https://www.last.fm/music/Neurosis",
    "oyentes_acumulados": 800,
    "reproducciones_acumuladas": 16000,
    "fuente": "Last.fm API",
    "fecha_obtencion": "2026-11-10T20:00:00+00:00",
}


class TestHU008LastFmRoute(unittest.IsolatedAsyncioTestCase):

    def crear_database(self, postulacion=POSTULACION):
        return SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(return_value=postulacion)
            )
        )

    async def test_identidad_confirmada_calcula_q_streaming(self):
        base = self.crear_database()

        with (
            patch.object(lastfm_route, "database", base),
            patch.object(
                lastfm_route,
                "extraer_id_artista_spotify",
                return_value=SPOTIFY_ID,
            ),
            patch.object(
                lastfm_route,
                "consultar_artista_spotify",
                new=AsyncMock(return_value=SPOTIFY),
            ),
            patch.object(
                lastfm_route,
                "obtener_metricas_lastfm_cache",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                lastfm_route,
                "consultar_artista_lastfm",
                new=AsyncMock(return_value=METRICAS),
            ) as consultar,
            patch.object(
                lastfm_route,
                "verificar_identidad_con_cache",
                new=AsyncMock(return_value=True),
            ),
            patch.object(
                lastfm_route,
                "guardar_metricas_lastfm_cache",
                new_callable=AsyncMock,
            ) as guardar,
        ):
            respuesta = await (
                lastfm_route.consultar_lastfm_postulacion(
                    POSTULACION_ID,
                    current_user={
                        "role": "ar",
                        "label_id": "sello_01",
                    },
                )
            )

            self.assertTrue(respuesta["identidad_confirmada"])
            self.assertEqual(respuesta["estado"], "verificada")

            self.assertEqual(
                respuesta["q_streaming"]["q_streaming"],
                70,
            )

            self.assertEqual(
                respuesta["q_streaming"]["puntaje_audiencia"],
                20,
            )

            self.assertEqual(
                respuesta["q_streaming"]["puntaje_fidelidad"],
                50,
            )

            self.assertEqual(
                respuesta["q_streaming"][
                    "ratio_reproducciones_oyente"
                ],
                20.0,
            )

            consultar.assert_awaited_once_with("Neurosis")
            guardar.assert_awaited_once()

    async def test_identidad_pendiente_no_calcula_puntaje(self):
        base = self.crear_database()

        with (
            patch.object(lastfm_route, "database", base),
            patch.object(
                lastfm_route,
                "extraer_id_artista_spotify",
                return_value=SPOTIFY_ID,
            ),
            patch.object(
                lastfm_route,
                "consultar_artista_spotify",
                new=AsyncMock(return_value=SPOTIFY),
            ),
            patch.object(
                lastfm_route,
                "obtener_metricas_lastfm_cache",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                lastfm_route,
                "consultar_artista_lastfm",
                new=AsyncMock(return_value=METRICAS),
            ),
            patch.object(
                lastfm_route,
                "verificar_identidad_con_cache",
                new=AsyncMock(return_value=False),
            ),
            patch.object(
                lastfm_route,
                "guardar_metricas_lastfm_cache",
                new_callable=AsyncMock,
            ) as guardar,
        ):
            respuesta = await (
                lastfm_route.consultar_lastfm_postulacion(
                    POSTULACION_ID,
                    current_user={
                        "role": "ar",
                        "label_id": "sello_01",
                    },
                )
            )

            self.assertFalse(respuesta["identidad_confirmada"])
            self.assertEqual(
                respuesta["estado"],
                "pendiente_verificacion",
            )
            self.assertIsNone(respuesta["q_streaming"])

            guardar.assert_not_awaited()

    async def test_artista_no_encontrado_recibe_cero(self):
        base = self.crear_database()

        with (
            patch.object(lastfm_route, "database", base),
            patch.object(
                lastfm_route,
                "extraer_id_artista_spotify",
                return_value=SPOTIFY_ID,
            ),
            patch.object(
                lastfm_route,
                "consultar_artista_spotify",
                new=AsyncMock(return_value=SPOTIFY),
            ),
            patch.object(
                lastfm_route,
                "obtener_metricas_lastfm_cache",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                lastfm_route,
                "consultar_artista_lastfm",
                new=AsyncMock(
                    side_effect=ArtistaLastFMNoEncontrado(
                        "Artista no encontrado"
                    )
                ),
            ),
            patch.object(
                lastfm_route,
                "verificar_identidad_con_cache",
                new_callable=AsyncMock,
            ) as verificar,
        ):
            respuesta = await (
                lastfm_route.consultar_lastfm_postulacion(
                    POSTULACION_ID,
                    current_user={
                        "role": "ar",
                        "label_id": "sello_01",
                    },
                )
            )

            self.assertIsNone(respuesta["lastfm"])
            self.assertEqual(
                respuesta["estado"],
                "perfil_no_encontrado",
            )
            self.assertEqual(
                respuesta["q_streaming"]["q_streaming"],
                0,
            )

            verificar.assert_not_awaited()

    async def test_error_lastfm_responde_502(self):
        base = self.crear_database()

        with (
            patch.object(lastfm_route, "database", base),
            patch.object(
                lastfm_route,
                "extraer_id_artista_spotify",
                return_value=SPOTIFY_ID,
            ),
            patch.object(
                lastfm_route,
                "consultar_artista_spotify",
                new=AsyncMock(return_value=SPOTIFY),
            ),
            patch.object(
                lastfm_route,
                "obtener_metricas_lastfm_cache",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                lastfm_route,
                "consultar_artista_lastfm",
                new=AsyncMock(
                    side_effect=RuntimeError(
                        "Last.fm no disponible"
                    )
                ),
            ),
        ):
            with self.assertRaises(HTTPException) as contexto:
                await lastfm_route.consultar_lastfm_postulacion(
                    POSTULACION_ID,
                    current_user={
                        "role": "ar",
                        "label_id": "sello_01",
                    },
                )

            self.assertEqual(contexto.exception.status_code, 502)

    async def test_rechazar_usuario_sin_rol_ar(self):
        with self.assertRaises(HTTPException) as contexto:
            await lastfm_route.consultar_lastfm_postulacion(
                POSTULACION_ID,
                current_user={
                    "role": "admin",
                    "label_id": "sello_01",
                },
            )

        self.assertEqual(contexto.exception.status_code, 403)

    async def test_rechazar_postulacion_de_otro_sello(self):
        base = self.crear_database(postulacion=None)

        with patch.object(lastfm_route, "database", base):
            with self.assertRaises(HTTPException) as contexto:
                await lastfm_route.consultar_lastfm_postulacion(
                    POSTULACION_ID,
                    current_user={
                        "role": "ar",
                        "label_id": "sello_02",
                    },
                )

            self.assertEqual(contexto.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
