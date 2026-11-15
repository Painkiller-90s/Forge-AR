
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.routes import viabilidad_route


POSTULACION_ID = "6af88df63a0d5615327d95ff"

EVALUACION_ID = ObjectId(
    "6af9114e012259e2824ef29c"
)

FECHA_GENERACION = datetime(
    2026, 11, 15, 1, 56, 30,
    tzinfo=timezone.utc,
)

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

    def crear_reporte(self):
        """Crea un reporte simulado con todos sus campos."""

        return {
            "_id": EVALUACION_ID,
            "postulacion_id": POSTULACION_ID,
            "sello_id": "sello_01",
            "evaluador_id": "usuario_123",
            "fecha_generacion": FECHA_GENERACION,
            "estado": "evaluable",

            "viabilidad": {
                "estado": "evaluable",
                "score": 81,
                "nivel_riesgo": "bajo",
                "dimensiones": {
                    "q_audio": 85,
                    "q_streaming": 90,
                },
            },

            "fuentes": {
                "spotify": {
                    "disponible": True,
                },
                "lastfm": {
                    "disponible": True,
                    "identidad_confirmada": True,
                },
                "instagram": {
                    "disponible": True,
                },
            },

            "datos_utilizados": {
                "press_kit": {
                    "nombre_artistico": "Artificial Brain",
                },
                "demos": [
                    {
                        "archivo_id": "demo_123",
                        "nombre": "Demo de prueba",
                        "storage_key": "demos/privado/demo.flac",
                    }
                ],
            },
        }

    # --------------------------------------------------
    # CONSULTAR REPORTE
    # --------------------------------------------------

    async def test_consultar_reporte_guardado(self):

        reporte = self.crear_reporte()
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

        # Identificación del reporte.
        self.assertEqual(
            resultado["evaluacion_id"],
            str(EVALUACION_ID),
        )

        self.assertEqual(
            resultado["postulacion_id"],
            POSTULACION_ID,
        )

        # Fecha y estado.
        self.assertEqual(
            resultado["fecha_generacion"],
            FECHA_GENERACION,
        )

        self.assertEqual(
            resultado["estado"],
            "evaluable",
        )

        # Resultado de viabilidad.
        self.assertEqual(
            resultado["viabilidad"]["score"],
            81,
        )

        self.assertEqual(
            resultado["viabilidad"]["nivel_riesgo"],
            "bajo",
        )

        # Fuentes utilizadas.
        self.assertTrue(
            resultado["fuentes"]["spotify"]["disponible"]
        )

        self.assertTrue(
            resultado["fuentes"]["lastfm"]["identidad_confirmada"]
        )

        # Datos utilizados.
        self.assertEqual(
            resultado["datos_utilizados"]["press_kit"]["nombre_artistico"],
            "Artificial Brain",
        )

        self.assertEqual(
            resultado["datos_utilizados"]["demos"][0]["nombre"],
            "Demo de prueba",
        )

        # No exponer claves internas de almacenamiento.
        self.assertNotIn(
            "storage_key",
            resultado["datos_utilizados"]["demos"][0],
        )

        # Verificar consulta a MongoDB.
        base.evaluaciones.find_one.assert_awaited_once_with(
            {
                "postulacion_id": POSTULACION_ID,
                "sello_id": "sello_01",
            },
            sort=[("fecha_generacion", -1)],
        )

    # --------------------------------------------------
    # REPORTE NO ENCONTRADO
    # --------------------------------------------------

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

        base.evaluaciones.find_one.assert_awaited_once()

    # --------------------------------------------------
    # AISLAMIENTO POR SELLO
    # --------------------------------------------------

    async def test_aislamiento_por_sello(self):

        reporte = self.crear_reporte()
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
            resultado["evaluacion_id"],
            str(EVALUACION_ID),
        )

        self.assertEqual(
            resultado["viabilidad"]["score"],
            81,
        )

    # --------------------------------------------------
    # VALIDACIONES DE AUTORIZACIÓN
    # --------------------------------------------------

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

    # --------------------------------------------------
    # VALIDACIÓN DEL IDENTIFICADOR
    # --------------------------------------------------

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
    
    async def test_fecha_generacion_naive_se_normaliza_utc(self):

        reporte = self.crear_reporte()

        # Simular la fecha recuperada desde MongoDB.
        reporte["fecha_generacion"] = datetime(
            2026, 11, 15, 1, 56, 30
        )

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

        fecha = resultado["fecha_generacion"]

        self.assertIsNotNone(fecha.tzinfo)

        self.assertEqual(
            fecha.utcoffset().total_seconds(),
            0,
        )

        self.assertTrue(
            fecha.isoformat().endswith("+00:00")
        )


if __name__ == "__main__":
    unittest.main()
