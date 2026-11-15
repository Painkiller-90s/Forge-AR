
import os
import unittest
from unittest.mock import patch

from bson import ObjectId
from fastapi import HTTPException
from pymongo import AsyncMongoClient

from app.config.settings import settings
from app.routes import postulacion_route
from app.services import audit_service
from app.schemas.postulacion_schema import (
    CambiarEstadoPostulacionRequest,
)


EJECUTAR_INTEGRACION = (
    os.getenv("RUN_MONGODB_INTEGRATION_TESTS") == "1"
)


@unittest.skipUnless(
    EJECUTAR_INTEGRACION,
    "Prueba de integración deshabilitada.",
)
class TestHU013TransaccionesMongo(
    unittest.IsolatedAsyncioTestCase
):

    async def asyncSetUp(self):

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
            self.client = None

            self.skipTest(
                "MongoDB no admite transacciones."
            )

        self.postulacion_id_obj = ObjectId()
        self.postulacion_id = str(
            self.postulacion_id_obj
        )

        self.usuario = {
            "_id": ObjectId(),
            "role": "ar",
            "label_id": "sello_hu013_test",
        }

        # Utilizar el mismo cliente y base de datos
        # en la ruta y en el servicio de auditoría.
        self._patchers = [
            patch.object(
                postulacion_route,
                "client",
                self.client,
            ),
            patch.object(
                postulacion_route,
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

        await self.database.postulaciones.insert_one({
            "_id": self.postulacion_id_obj,
            "sello_id": "sello_hu013_test",
            "estado": "recibida",
        })

    async def asyncTearDown(self):

        try:
            if self.client is not None:

                await self.database.postulaciones.delete_one({
                    "_id": self.postulacion_id_obj
                })

                await self.database.auditorias.delete_many({
                    "postulacion_id": self.postulacion_id
                })

        finally:

            for parche in reversed(self._patchers):
                parche.stop()

            if self.client is not None:
                await self.client.close()

    async def test_transaccion_exitosa(self):

        resultado = await (
            postulacion_route.cambiar_estado_postulacion(
                self.postulacion_id,
                CambiarEstadoPostulacionRequest(
                    estado="en_revision"
                ),
                current_user=self.usuario,
            )
        )

        postulacion = await (
            self.database.postulaciones.find_one({
                "_id": self.postulacion_id_obj
            })
        )

        auditoria = await (
            self.database.auditorias.find_one({
                "postulacion_id": self.postulacion_id,
                "accion": "CAMBIO_ESTADO_POSTULACION",
            })
        )

        self.assertEqual(
            resultado["estado_nuevo"],
            "en_revision",
        )

        self.assertEqual(
            postulacion["estado"],
            "en_revision",
        )

        self.assertIsNotNone(auditoria)

        self.assertEqual(
            auditoria["estado_anterior"],
            "recibida",
        )

        self.assertEqual(
            auditoria["estado_nuevo"],
            "en_revision",
        )

        self.assertEqual(
            auditoria["usuario_id"],
            str(self.usuario["_id"]),
        )

    async def test_revertir_estado_si_falla_auditoria(self):

        async def registrar_y_fallar(**kwargs):

            # Ejecutar primero el registro real.
            await audit_service.registrar_auditoria(
                **kwargs
            )

            # Simular un error después de insertar.
            raise RuntimeError(
                "Fallo simulado de auditoría."
            )

        with patch.object(
            postulacion_route,
            "registrar_auditoria",
            new=registrar_y_fallar,
        ):

            with self.assertRaises(HTTPException) as contexto:

                await (
                    postulacion_route.cambiar_estado_postulacion(
                        self.postulacion_id,
                        CambiarEstadoPostulacionRequest(
                            estado="en_revision"
                        ),
                        current_user=self.usuario,
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            500,
        )

        # MongoDB debe conservar el estado original.
        postulacion = await (
            self.database.postulaciones.find_one({
                "_id": self.postulacion_id_obj
            })
        )

        self.assertEqual(
            postulacion["estado"],
            "recibida",
        )

        # La auditoría también debe haberse revertido.
        cantidad_auditorias = await (
            self.database.auditorias.count_documents({
                "postulacion_id": self.postulacion_id,
            })
        )

        self.assertEqual(
            cantidad_auditorias,
            0,
        )


if __name__ == "__main__":
    unittest.main()
