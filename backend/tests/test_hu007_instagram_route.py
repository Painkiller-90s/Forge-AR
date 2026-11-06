
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.routes import instagram_route


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"

POSTULACION_SIMULADA = {
    "_id": ObjectId(POSTULACION_ID),
    "sello_id": "sello_01",
    "press_kit": {
        "instagram_url": "https://www.instagram.com/scarcity.noise/"
    },
}

METRICAS_SIMULADAS = {
    "username": "scarcity.noise",
    "seguidores": 2903,
    "fuente": "Apify Instagram Profile Scraper",
    "fecha_obtencion": "2026-11-04T22:18:38Z",
    "estado_metricas": "actualizadas",
}


class TestHU007InstagramRoute(unittest.IsolatedAsyncioTestCase):

    async def test_consulta_guarda_metricas(self):
        base_simulada = SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(
                    return_value=POSTULACION_SIMULADA
                )
            )
        )

        with (
            patch.object(
                instagram_route, "database", base_simulada
            ),
            patch.object(
                instagram_route,
                "obtener_metricas_instagram",
                new_callable=AsyncMock,
            ) as consultar,
            patch.object(
                instagram_route,
                "guardar_metricas_validas",
                new_callable=AsyncMock,
            ) as guardar,
        ):
            consultar.return_value = dict(METRICAS_SIMULADAS)

            respuesta = (
                await instagram_route.consultar_instagram_postulacion(
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

            consultar.assert_awaited_once_with(
                "https://www.instagram.com/scarcity.noise/"
            )

            guardar.assert_awaited_once_with(
                postulacion_id=POSTULACION_ID,
                sello_id="sello_01",
                plataforma="instagram",
                cuenta_id="scarcity.noise",
                metricas=METRICAS_SIMULADAS,
            )

    async def test_error_al_guardar_metricas(self):
        base_simulada = SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(
                    return_value=POSTULACION_SIMULADA
                )
            )
        )

        with (
            patch.object(
                instagram_route, "database", base_simulada
            ),
            patch.object(
                instagram_route,
                "obtener_metricas_instagram",
                new=AsyncMock(
                    return_value=dict(METRICAS_SIMULADAS)
                ),
            ),
            patch.object(
                instagram_route,
                "guardar_metricas_validas",
                new=AsyncMock(
                    side_effect=RuntimeError(
                        "Fallo simulado de MongoDB"
                    )
                ),
            ),
            patch.object(
                instagram_route.logger, "error"
            ) as registrar_error,
        ):
            with self.assertRaises(
                HTTPException
            ) as contexto:
                await instagram_route.consultar_instagram_postulacion(
                    POSTULACION_ID,
                    current_user={
                        "role": "ar",
                        "label_id": "sello_01",
                    },
                )

            self.assertEqual(
                contexto.exception.status_code,
                500,
            )

            registrar_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
