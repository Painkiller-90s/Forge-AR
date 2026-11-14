
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId

from app.services import recopilacion_evaluacion_service as service


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"
SPOTIFY_ID = "1234567890123456789012"
FECHA = "2026-11-14T12:00:00+00:00"

POSTULACION = {
    "_id": ObjectId(POSTULACION_ID),
    "sello_id": "sello_01",
    "press_kit": {
        "spotify_url": (
            f"https://open.spotify.com/artist/{SPOTIFY_ID}"
        ),
        "instagram_url": (
            "https://www.instagram.com/mi.banda/"
        ),
    },
}

PERFIL_SPOTIFY = {
    "spotify_id": SPOTIFY_ID,
    "nombre": "Mi Banda",
    "fecha_obtencion": FECHA,
}

CATALOGO_SPOTIFY = {
    "albumes": [],
    "canciones": [],
}

METRICAS_INSTAGRAM = {
    "username": "mi.banda",
    "seguidores": 2000,
    "publicaciones": [],
    "fuente": "Apify Instagram Profile Scraper",
    "fecha_obtencion": FECHA,
}

METRICAS_LASTFM = {
    "nombre": "Mi Banda",
    "mbid": "mbid-ejemplo",
    "url": "https://www.last.fm/music/Mi+Banda",
    "oyentes_acumulados": 800,
    "reproducciones_acumuladas": 16000,
    "fuente": "Last.fm API",
    "fecha_obtencion": FECHA,
}


class TestHU009RecopilacionEvaluacion(
    unittest.IsolatedAsyncioTestCase
):

    async def test_recopilar_metricas_completas(self):

        base_simulada = SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(return_value=POSTULACION)
            )
        )

        with (
            patch.object(
                service,
                "database",
                base_simulada,
            ),
            patch.object(
                service,
                "extraer_id_artista_spotify",
                return_value=SPOTIFY_ID,
            ),
            patch.object(
                service,
                "consultar_artista_spotify",
                new_callable=AsyncMock,
                return_value=PERFIL_SPOTIFY,
            ),
            patch.object(
                service,
                "consultar_catalogo_spotify",
                new_callable=AsyncMock,
                return_value=CATALOGO_SPOTIFY,
            ),
            patch.object(
                service,
                "extraer_usuario_instagram",
                return_value="mi.banda",
            ),
            patch.object(
                service,
                "obtener_metricas_instagram",
                new_callable=AsyncMock,
                return_value=METRICAS_INSTAGRAM,
            ),
            patch.object(
                service,
                "guardar_metricas_validas",
                new_callable=AsyncMock,
            ) as guardar_metricas,
            patch.object(
                service,
                "obtener_metricas_lastfm_cache",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch.object(
                service,
                "consultar_artista_lastfm",
                new_callable=AsyncMock,
                return_value=METRICAS_LASTFM,
            ),
            patch.object(
                service,
                "verificar_identidad_con_cache",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch.object(
                service,
                "guardar_metricas_lastfm_cache",
                new_callable=AsyncMock,
            ) as guardar_lastfm,
        ):

            resultado = await service.recopilar_metricas_evaluacion(
                POSTULACION_ID,
                "sello_01",
            )

            self.assertIsNotNone(resultado)

            self.assertIsNotNone(resultado["spotify"])
            self.assertIsNotNone(resultado["instagram"])
            self.assertIsNotNone(resultado["lastfm"])

            self.assertTrue(
                resultado["identidad_confirmada"]
            )

            self.assertTrue(
                resultado["perfil_lastfm_encontrado"]
            )

            self.assertEqual(
                resultado["spotify"]["perfil"]["nombre"],
                "Mi Banda",
            )

            self.assertEqual(
                resultado["instagram"]["seguidores"],
                2000,
            )

            self.assertEqual(
                resultado["lastfm"]["mbid"],
                "mbid-ejemplo",
            )

            self.assertEqual(
                guardar_metricas.await_count,
                2,
            )

            guardar_lastfm.assert_awaited_once()

    async def test_respaldo_spotify(self):

        respaldo = {
            "perfil": PERFIL_SPOTIFY,
            "catalogo": CATALOGO_SPOTIFY,
            "fuente": "Spotify Web API",
            "fecha_obtencion": FECHA,
            "estado_metricas": "desactualizadas",
        }

        with (
            patch.object(
                service,
                "extraer_id_artista_spotify",
                return_value=SPOTIFY_ID,
            ),
            patch.object(
                service,
                "consultar_artista_spotify",
                new_callable=AsyncMock,
                side_effect=RuntimeError("Spotify no disponible"),
            ),
            patch.object(
                service,
                "consultar_catalogo_spotify",
                new_callable=AsyncMock,
            ) as consultar_catalogo,
            patch.object(
                service,
                "recuperar_ultimas_metricas",
                new_callable=AsyncMock,
                return_value=respaldo,
            ) as recuperar,
            patch.object(service.logger, "exception"),
        ):

            resultado, spotify_id = await service._obtener_spotify(
                POSTULACION_ID,
                "sello_01",
                POSTULACION["press_kit"]["spotify_url"],
            )

            self.assertEqual(spotify_id, SPOTIFY_ID)
            self.assertEqual(resultado, respaldo)

            recuperar.assert_awaited_once()
            consultar_catalogo.assert_not_awaited()

    async def test_respaldo_instagram(self):

        respaldo = {
            **METRICAS_INSTAGRAM,
            "estado_metricas": "desactualizadas",
        }

        with (
            patch.object(
                service,
                "extraer_usuario_instagram",
                return_value="mi.banda",
            ),
            patch.object(
                service,
                "obtener_metricas_instagram",
                new_callable=AsyncMock,
                side_effect=RuntimeError("Apify no disponible"),
            ),
            patch.object(
                service,
                "recuperar_ultimas_metricas",
                new_callable=AsyncMock,
                return_value=respaldo,
            ) as recuperar,
            patch.object(service.logger, "exception"),
        ):

            resultado = await service._obtener_instagram(
                POSTULACION_ID,
                "sello_01",
                POSTULACION["press_kit"]["instagram_url"],
            )

            self.assertEqual(resultado, respaldo)
            self.assertEqual(
                resultado["estado_metricas"],
                "desactualizadas",
            )

            recuperar.assert_awaited_once()

    async def test_lastfm_cache_vigente(self):

        metricas = dict(METRICAS_LASTFM)

        with (
            patch.object(
                service,
                "obtener_metricas_lastfm_cache",
                new_callable=AsyncMock,
                return_value=metricas,
            ),
            patch.object(
                service,
                "consultar_artista_lastfm",
                new_callable=AsyncMock,
            ) as consultar,
            patch.object(
                service,
                "verificar_identidad_con_cache",
                new_callable=AsyncMock,
                return_value=True,
            ) as verificar,
            patch.object(
                service,
                "guardar_metricas_lastfm_cache",
                new_callable=AsyncMock,
            ) as guardar,
        ):

            resultado, encontrado, identidad = (
                await service._obtener_lastfm(
                    POSTULACION_ID,
                    SPOTIFY_ID,
                    "Mi Banda",
                )
            )

            self.assertTrue(encontrado)
            self.assertTrue(identidad)

            self.assertEqual(
                resultado["estado_metricas"],
                "actualizadas",
            )

            consultar.assert_not_awaited()
            verificar.assert_awaited_once()
            guardar.assert_not_awaited()

    async def test_lastfm_respaldo_historico(self):

        respaldo = dict(METRICAS_LASTFM)

        with (
            patch.object(
                service,
                "obtener_metricas_lastfm_cache",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch.object(
                service,
                "consultar_artista_lastfm",
                new_callable=AsyncMock,
                side_effect=RuntimeError("Last.fm no disponible"),
            ),
            patch.object(
                service,
                "recuperar_ultimas_metricas_lastfm_cache",
                new_callable=AsyncMock,
                return_value=respaldo,
            ) as recuperar,
            patch.object(
                service,
                "verificar_identidad_con_cache",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch.object(
                service,
                "guardar_metricas_lastfm_cache",
                new_callable=AsyncMock,
            ) as guardar,
            patch.object(service.logger, "exception"),
        ):

            resultado, encontrado, identidad = (
                await service._obtener_lastfm(
                    POSTULACION_ID,
                    SPOTIFY_ID,
                    "Mi Banda",
                )
            )

            self.assertTrue(encontrado)
            self.assertTrue(identidad)

            self.assertEqual(
                resultado["estado_metricas"],
                "desactualizadas",
            )

            recuperar.assert_awaited_once()
            guardar.assert_not_awaited()

    async def test_lastfm_artista_no_encontrado(self):

        with (
            patch.object(
                service,
                "obtener_metricas_lastfm_cache",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch.object(
                service,
                "consultar_artista_lastfm",
                new_callable=AsyncMock,
                side_effect=service.ArtistaLastFMNoEncontrado(
                    "Artista no encontrado"
                ),
            ),
            patch.object(
                service,
                "recuperar_ultimas_metricas_lastfm_cache",
                new_callable=AsyncMock,
            ) as recuperar,
            patch.object(
                service,
                "verificar_identidad_con_cache",
                new_callable=AsyncMock,
            ) as verificar,
        ):

            resultado, encontrado, identidad = (
                await service._obtener_lastfm(
                    POSTULACION_ID,
                    SPOTIFY_ID,
                    "Mi Banda",
                )
            )

            self.assertIsNone(resultado)
            self.assertFalse(encontrado)
            self.assertFalse(identidad)

            recuperar.assert_not_awaited()
            verificar.assert_not_awaited()

    async def test_lastfm_identidad_no_confirmada(self):

        metricas = dict(METRICAS_LASTFM)

        with (
            patch.object(
                service,
                "obtener_metricas_lastfm_cache",
                new_callable=AsyncMock,
                return_value=metricas,
            ),
            patch.object(
                service,
                "verificar_identidad_con_cache",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):

            resultado, encontrado, identidad = (
                await service._obtener_lastfm(
                    POSTULACION_ID,
                    SPOTIFY_ID,
                    "Mi Banda",
                )
            )

            self.assertIsNotNone(resultado)
            self.assertTrue(encontrado)
            self.assertFalse(identidad)

    async def test_postulacion_no_encontrada(self):

        base_simulada = SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(return_value=None)
            )
        )

        with patch.object(
            service,
            "database",
            base_simulada,
        ):

            resultado = await service.recopilar_metricas_evaluacion(
                POSTULACION_ID,
                "sello_01",
            )

            self.assertIsNone(resultado)


if __name__ == "__main__":
    unittest.main()
