
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.routes import instagram_route


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"

POSTULACION = {
    "_id": ObjectId(POSTULACION_ID),
    "sello_id": "sello_01",
    "press_kit": {
        "instagram_url": "https://www.instagram.com/scarcity.noise/"
    },
}

RESPALDO = {
    "username": "scarcity.noise",
    "seguidores": 2903,
    "fuente": "Apify Instagram Profile Scraper",
    "fecha_obtencion": "2026-11-04T22:57:56Z",
    "estado_metricas": "desactualizadas",
}


class TestHU007InstagramFallback(unittest.IsolatedAsyncioTestCase):

    async def test_fallo_apify_con_respaldo(self):
        base_simulada = SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(return_value=POSTULACION)
            )
        )

        with (
            patch.object(instagram_route, "database", base_simulada),
            patch.object(
                instagram_route,
                "obtener_metricas_instagram",
                new=AsyncMock(
                    side_effect=RuntimeError("Apify no disponible")
                ),
            ),
            patch.object(
                instagram_route,
                "recuperar_ultimas_metricas",
                new_callable=AsyncMock,
            ) as recuperar,
            patch.object(
                instagram_route,
                "guardar_metricas_validas",
                new_callable=AsyncMock,
            ) as guardar,
            patch.object(
                instagram_route.logger,
                "error",
            ) as registrar_error,
        ):
            recuperar.return_value = dict(RESPALDO)

            respuesta = await (
                instagram_route.consultar_instagram_postulacion(
                    POSTULACION_ID,
                    current_user={
                        "role": "ar",
                        "label_id": "sello_01",
                    },
                )
            )

            self.assertEqual(
                respuesta["postulacion_id"],
                POSTULACION_ID,
            )
            self.assertEqual(
                respuesta["instagram"]["seguidores"],
                2903,
            )
            self.assertEqual(
                respuesta["instagram"]["estado_metricas"],
                "desactualizadas",
            )
            self.assertEqual(
                respuesta["instagram"]["fecha_obtencion"],
                RESPALDO["fecha_obtencion"],
            )

            recuperar.assert_awaited_once_with(
                postulacion_id=POSTULACION_ID,
                sello_id="sello_01",
                plataforma="instagram",
                cuenta_id="scarcity.noise",
            )

            guardar.assert_not_awaited()
            # CA07: comprobar el registro del error de Instagram.
            registrar_error.assert_called_once()

            argumentos = registrar_error.call_args.args

            self.assertIn("HU007", argumentos[0])
            self.assertEqual(argumentos[1], POSTULACION_ID)
            self.assertEqual(argumentos[2], "RuntimeError")

    async def test_fallo_apify_sin_respaldo(self):
        base_simulada = SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(return_value=POSTULACION)
            )
        )

        with (
            patch.object(instagram_route, "database", base_simulada),
            patch.object(
                instagram_route,
                "obtener_metricas_instagram",
                new=AsyncMock(
                    side_effect=RuntimeError("Apify no disponible")
                ),
            ),
            patch.object(
                instagram_route,
                "recuperar_ultimas_metricas",
                new=AsyncMock(return_value=None),
            ),
            patch.object(instagram_route.logger, "error"),
        ):
            with self.assertRaises(HTTPException) as contexto:
                await instagram_route.consultar_instagram_postulacion(
                    POSTULACION_ID,
                    current_user={
                        "role": "ar",
                        "label_id": "sello_01",
                    },
                )

            self.assertEqual(
                contexto.exception.status_code,
                502,
            )
            self.assertEqual(
                contexto.exception.detail,
                "No fue posible obtener las métricas de Instagram.",
            )


if __name__ == "__main__":
    unittest.main()
