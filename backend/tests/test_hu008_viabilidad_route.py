
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.routes import viabilidad_route


POSTULACION_ID = "6af88df63a0d5615327d95ff"

USUARIO_AR = {
    "role": "ar",
    "label_id": "sello_01",
}


class TestHU008ViabilidadRoute(
    unittest.IsolatedAsyncioTestCase
):

    def crear_database(self, reporte=None):
        return SimpleNamespace(
            evaluaciones=SimpleNamespace(
                find_one=AsyncMock(
                    return_value=reporte
                ),
            )
        )

    async def test_consultar_reporte_guardado(self):
        reporte = {
            "postulacion_id": POSTULACION_ID,
            "sello_id": "sello_01",
            "estado": "evaluable",
            "viabilidad": {
                "estado": "evaluable",
                "score": 81,
                "nivel_riesgo": "bajo",
            },
            "fuentes": {
                "spotify": {"disponible": True},
                "lastfm": {
                    "disponible": True,
                    "identidad_confirmada": True,
                },
                "instagram": {"disponible": True},
            },
        }

        base = self.crear_database(reporte)

        with patch.object(
            viabilidad_route,
            "database",
            base,
        ):
            resultado = await (
                viabilidad_route.consultar_viabilidad_postulacion(
                    POSTULACION_ID,
                    current_user=USUARIO_AR,
                )
            )

        self.assertEqual(
            resultado["postulacion_id"],
            POSTULACION_ID,
        )

        self.assertEqual(
            resultado["viabilidad"]["score"],
            81,
        )

        self.assertEqual(
            resultado["viabilidad"]["nivel_riesgo"],
            "bajo",
        )

        base.evaluaciones.find_one.assert_awaited_once_with(
            {
                "postulacion_id": POSTULACION_ID,
                "sello_id": "sello_01",
            },
            sort=[("fecha_generacion", -1)],
        )

    async def test_sin_reporte_devuelve_404(self):
        base = self.crear_database()

        with patch.object(
            viabilidad_route,
            "database",
            base,
        ):
            with self.assertRaises(HTTPException) as contexto:
                await (
                    viabilidad_route.consultar_viabilidad_postulacion(
                        POSTULACION_ID,
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            404,
        )


    async def test_aislamiento_por_sello(self):
        reporte = {
            "postulacion_id": POSTULACION_ID,
            "sello_id": "sello_01",
            "estado": "evaluable",
            "viabilidad": {
                "estado": "evaluable",
                "score": 81,
                "nivel_riesgo": "bajo",
            },
            "fuentes": {
                "spotify": {"disponible": True},
                "lastfm": {"disponible": True},
                "instagram": {"disponible": True},
            },
        }

        base = self.crear_database(reporte)

        with patch.object(
            viabilidad_route,
            "database",
            base,
        ):
            resultado = await (
                viabilidad_route.consultar_viabilidad_postulacion(
                    POSTULACION_ID,
                    current_user=USUARIO_AR,
                )
            )

        filtro = base.evaluaciones.find_one.call_args.args[0]

        self.assertEqual(
            filtro["postulacion_id"],
            POSTULACION_ID,
        )

        self.assertEqual(
            filtro["sello_id"],
            "sello_01",
        )

        self.assertEqual(
            resultado["viabilidad"]["score"],
            81,
        )


    async def test_rechazar_usuario_sin_rol_ar(self):
        base = self.crear_database()

        with patch.object(
            viabilidad_route,
            "database",
            base,
        ):
            with self.assertRaises(HTTPException) as contexto:
                await (
                    viabilidad_route.consultar_viabilidad_postulacion(
                        POSTULACION_ID,
                        current_user={
                            "role": "admin",
                            "label_id": "sello_01",
                        },
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            403,
        )

        base.evaluaciones.find_one.assert_not_awaited()

    async def test_rechazar_usuario_sin_sello(self):
        base = self.crear_database()

        with patch.object(
            viabilidad_route,
            "database",
            base,
        ):
            with self.assertRaises(HTTPException) as contexto:
                await (
                    viabilidad_route.consultar_viabilidad_postulacion(
                        POSTULACION_ID,
                        current_user={
                            "role": "ar",
                            "label_id": None,
                        },
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            403,
        )

        base.evaluaciones.find_one.assert_not_awaited()

    async def test_rechazar_id_invalido(self):
        base = self.crear_database()

        with patch.object(
            viabilidad_route,
            "database",
            base,
        ):
            with self.assertRaises(HTTPException) as contexto:
                await (
                    viabilidad_route.consultar_viabilidad_postulacion(
                        "id-invalido",
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            400,
        )

        base.evaluaciones.find_one.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
