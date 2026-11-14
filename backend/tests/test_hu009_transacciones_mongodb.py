
import os
import unittest
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException
from pymongo import AsyncMongoClient

from app.config.settings import settings
from app.routes import evaluacion_route
from app.services import audit_service


EJECUTAR_INTEGRACION = (
    os.getenv("RUN_MONGODB_INTEGRATION_TESTS") == "1"
)


@unittest.skipUnless(
    EJECUTAR_INTEGRACION,
    "Prueba de integración deshabilitada.",
)
class TestHU009TransaccionesMongo(
    unittest.IsolatedAsyncioTestCase
):

    async def asyncSetUp(self):

        # Crear un cliente independiente para este ciclo de eventos.
        self.client = AsyncMongoClient(
            settings.mongodb_url
        )

        self.database = self.client[
            settings.mongodb_db_name
        ]

        self._patchers = []

        await self.client.admin.command("ping")

        informacion = await self.client.admin.command({
            "hello": 1
        })

        if (
            not informacion.get("setName")
            and informacion.get("msg") != "isdbgrid"
        ):
            await self.client.close()
            self.skipTest(
                "MongoDB no admite transacciones."
            )

        self.postulacion_id = str(ObjectId())

        self.usuario = {
            "_id": ObjectId(),
            "role": "ar",
            "label_id": "sello_hu009_test",
        }

        # Utilizar el mismo cliente y base de datos
        # en la ruta y en el servicio de auditoría.
        self._patchers = [
            patch.object(
                evaluacion_route,
                "client",
                self.client,
            ),
            patch.object(
                evaluacion_route,
                "database",
                self.database,
            ),
            patch.object(
                audit_service,
                "database",
                self.database,
            ),
        ]

        for parche in self._patchers:
            parche.start()

    async def asyncTearDown(self):

        try:
            if hasattr(self, "postulacion_id"):

                await self.database.evaluaciones.delete_many({
                    "postulacion_id": self.postulacion_id
                })

                await self.database.auditorias.delete_many({
                    "postulacion_id": self.postulacion_id
                })

        finally:

            for parche in reversed(self._patchers):
                parche.stop()

            if getattr(self, "client", None) is not None:
                await self.client.close()

    def crear_evaluacion(self):

        return {
            "postulacion_id": self.postulacion_id,

            "viabilidad": {
                "estado": "evaluable",
                "score": 80.5,
                "nivel_riesgo": "bajo",
                "dimensiones": {},
                "aportes": {},
                "dimensiones_faltantes": [],
                "motivos_no_evaluable": [],
            },

            "fuentes": {},

            "datos_utilizados": {
                "press_kit": {},
                "demos": [],
                "spotify": {},
                "lastfm": {},
                "instagram": {},
            },
        }

    async def test_transaccion_exitosa(self):

        with patch.object(
            evaluacion_route,
            "generar_evaluacion_actual",
            new=AsyncMock(
                return_value=self.crear_evaluacion()
            ),
        ):

            resultado = await (
                evaluacion_route.generar_reporte_evaluacion(
                    self.postulacion_id,
                    current_user=self.usuario,
                )
            )

        evaluacion_id = resultado["evaluacion_id"]

        reporte = await self.database.evaluaciones.find_one({
            "_id": ObjectId(evaluacion_id)
        })

        auditoria = await self.database.auditorias.find_one({
            "recurso_id": evaluacion_id,
            "accion": "GENERACION_EVALUACION",
        })

        self.assertIsNotNone(reporte)
        self.assertIsNotNone(auditoria)

        self.assertEqual(
            reporte["postulacion_id"],
            self.postulacion_id,
        )

        self.assertEqual(
            auditoria["postulacion_id"],
            self.postulacion_id,
        )

    async def test_revertir_reporte_si_falla_auditoria(self):

        async def registrar_y_fallar(**kwargs):

            # Ejecutar el registro real de auditoría.
            await audit_service.registrar_auditoria(
                **kwargs
            )

            # Simular un fallo después de insertar.
            raise RuntimeError(
                "Fallo simulado después de insertar auditoría."
            )

        with (
            patch.object(
                evaluacion_route,
                "generar_evaluacion_actual",
                new=AsyncMock(
                    return_value=self.crear_evaluacion()
                ),
            ),
            patch.object(
                evaluacion_route,
                "registrar_auditoria",
                new=registrar_y_fallar,
            ),
        ):

            with self.assertRaises(HTTPException) as contexto:

                await (
                    evaluacion_route.generar_reporte_evaluacion(
                        self.postulacion_id,
                        current_user=self.usuario,
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            500,
        )

        # Verificar que MongoDB revirtió ambas inserciones.
        reportes = await self.database.evaluaciones.count_documents({
            "postulacion_id": self.postulacion_id
        })

        auditorias = await self.database.auditorias.count_documents({
            "postulacion_id": self.postulacion_id
        })

        self.assertEqual(reportes, 0)
        self.assertEqual(auditorias, 0)


if __name__ == "__main__":
    unittest.main()
