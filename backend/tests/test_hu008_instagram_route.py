
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId

from app.routes import instagram_route


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"

POSTULACION = {
    "_id": ObjectId(POSTULACION_ID),
    "sello_id": "sello_01",
    "press_kit": {
        "instagram_url": "https://www.instagram.com/banda.prueba/"
    },
}

METRICAS = {
    "username": "banda.prueba",
    "seguidores": 2000,
    "publicaciones_totales": 3,
    "publicaciones": [
        {"likes": 80, "comentarios": 20, "es_propia": True},
        {"likes": 100, "comentarios": 0, "es_propia": True},
        {"likes": 60, "comentarios": 20, "es_propia": True},
    ],
    "fuente": "Apify Instagram Profile Scraper",
    "fecha_obtencion": "2026-11-12T12:00:00Z",
    "estado_metricas": "actualizadas",
}

USUARIO_AR = {
    "role": "ar",
    "label_id": "sello_01",
}


class TestHU008InstagramRoute(unittest.IsolatedAsyncioTestCase):

    def crear_base(self):
        return SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(return_value=POSTULACION)
            )
        )

    async def test_consulta_calcula_q_rrss(self):
        with (
            patch.object(
                instagram_route,
                "database",
                self.crear_base(),
            ),
            patch.object(
                instagram_route,
                "obtener_metricas_instagram",
                new=AsyncMock(return_value=dict(METRICAS)),
            ),
            patch.object(
                instagram_route,
                "guardar_metricas_validas",
                new_callable=AsyncMock,
            ) as guardar,
        ):
            respuesta = await (
                instagram_route.consultar_instagram_postulacion(
                    POSTULACION_ID,
                    current_user=USUARIO_AR,
                )
            )

            resultado = respuesta["q_rrss"]

            self.assertEqual(resultado["q_rrss"], 80)
            self.assertEqual(resultado["puntaje_likes"], 40)
            self.assertEqual(resultado["puntaje_comentarios"], 40)
            self.assertEqual(resultado["publicaciones_evaluadas"], 3)

            self.assertEqual(
                respuesta["instagram"]["seguidores"],
                2000,
            )

            guardar.assert_awaited_once()

    async def test_respaldo_desactualizado_calcula_q_rrss(self):
        respaldo = dict(METRICAS)
        respaldo["estado_metricas"] = "desactualizadas"

        with (
            patch.object(
                instagram_route,
                "database",
                self.crear_base(),
            ),
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
                new=AsyncMock(return_value=respaldo),
            ),
            patch.object(
                instagram_route,
                "guardar_metricas_validas",
                new_callable=AsyncMock,
            ) as guardar,
            patch.object(instagram_route.logger, "error"),
        ):
            respuesta = await (
                instagram_route.consultar_instagram_postulacion(
                    POSTULACION_ID,
                    current_user=USUARIO_AR,
                )
            )

            self.assertEqual(
                respuesta["q_rrss"]["q_rrss"],
                80,
            )

            self.assertEqual(
                respuesta["q_rrss"]["estado_metricas"],
                "desactualizadas",
            )

            self.assertEqual(
                respuesta["q_rrss"]["fecha_obtencion"],
                respaldo["fecha_obtencion"],
            )

            guardar.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
