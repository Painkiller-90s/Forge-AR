
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services.metricas_cache_service import (
    guardar_metricas_validas,
    recuperar_ultimas_metricas,
)


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"
SELLO_ID = "sello_01"
CUENTA_ID = "scarcity.noise"

METRICAS = {
    "username": CUENTA_ID,
    "seguidores": 2903,
    "fuente": "Apify Instagram Profile Scraper",
    "fecha_obtencion": "2026-11-04T22:18:38Z",
    "estado_metricas": "actualizadas",
}


class TestMetricasCacheService(unittest.IsolatedAsyncioTestCase):

    async def test_guardar_metricas_validas(self):
        coleccion = SimpleNamespace(
            update_one=AsyncMock()
        )

        base_simulada = SimpleNamespace(
            metricas_externas=coleccion
        )

        with patch(
            "app.services.metricas_cache_service.database",
            base_simulada,
        ):
            await guardar_metricas_validas(
                POSTULACION_ID,
                SELLO_ID,
                "instagram",
                CUENTA_ID,
                METRICAS,
            )

        filtro, actualizacion = coleccion.update_one.await_args.args

        self.assertEqual(filtro["postulacion_id"], POSTULACION_ID)
        self.assertEqual(filtro["sello_id"], SELLO_ID)
        self.assertEqual(filtro["plataforma"], "instagram")
        self.assertEqual(actualizacion["$set"]["cuenta_id"], CUENTA_ID)
        self.assertEqual(actualizacion["$set"]["metricas"], METRICAS)
        self.assertTrue(coleccion.update_one.await_args.kwargs["upsert"])

    async def test_recuperar_metricas_desactualizadas(self):
        coleccion = SimpleNamespace(
            find_one=AsyncMock(return_value={
                "metricas": dict(METRICAS)
            })
        )

        base_simulada = SimpleNamespace(
            metricas_externas=coleccion
        )

        with patch(
            "app.services.metricas_cache_service.database",
            base_simulada,
        ):
            resultado = await recuperar_ultimas_metricas(
                POSTULACION_ID,
                SELLO_ID,
                "instagram",
                CUENTA_ID,
            )

        self.assertEqual(resultado["seguidores"], 2903)
        self.assertEqual(
            resultado["estado_metricas"],
            "desactualizadas",
        )
        self.assertEqual(
            resultado["fecha_obtencion"],
            METRICAS["fecha_obtencion"],
        )

        filtro = coleccion.find_one.await_args.args[0]
        self.assertEqual(filtro["sello_id"], SELLO_ID)
        self.assertEqual(filtro["cuenta_id"], CUENTA_ID)

    async def test_sin_metricas_almacenadas(self):
        coleccion = SimpleNamespace(
            find_one=AsyncMock(return_value=None)
        )

        with patch(
            "app.services.metricas_cache_service.database",
            SimpleNamespace(metricas_externas=coleccion),
        ):
            resultado = await recuperar_ultimas_metricas(
                POSTULACION_ID,
                SELLO_ID,
                "instagram",
                CUENTA_ID,
            )

        self.assertIsNone(resultado)

    async def test_rechazar_metricas_invalidas(self):
        coleccion = SimpleNamespace(
            update_one=AsyncMock()
        )

        with patch(
            "app.services.metricas_cache_service.database",
            SimpleNamespace(metricas_externas=coleccion),
        ):
            with self.assertRaises(ValueError):
                await guardar_metricas_validas(
                    POSTULACION_ID,
                    SELLO_ID,
                    "plataforma_invalida",
                    CUENTA_ID,
                    METRICAS,
                )

            with self.assertRaises(ValueError):
                await guardar_metricas_validas(
                    POSTULACION_ID,
                    SELLO_ID,
                    "instagram",
                    CUENTA_ID,
                    {"seguidores": 2903},
                )

        coleccion.update_one.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
