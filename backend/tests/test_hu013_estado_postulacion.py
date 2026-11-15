
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, ANY, patch

from bson import ObjectId
from fastapi import HTTPException
from pydantic import ValidationError

from app.routes import postulacion_route
from app.schemas.postulacion_schema import (
    CambiarEstadoPostulacionRequest,
)


POSTULACION_ID = "6af88df63a0d5615327d95ff"

USUARIO_AR = {
    "_id": ObjectId("6af88df63a0d5615327d9501"),
    "role": "ar",
    "label_id": "sello_01",
}


# --------------------------------------------------
# SIMULACIÓN DE TRANSACCIONES
# --------------------------------------------------

class FakeSession:

    async def with_transaction(self, callback):
        return await callback(self)


class FakeBoundSession:

    async def __aenter__(self):
        return FakeSession()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSessionFactory:

    def bind(self):
        return FakeBoundSession()


class FakeClient:

    def start_session(self):
        return FakeSessionFactory()


# --------------------------------------------------
# PRUEBAS HU013
# --------------------------------------------------

class TestHU013EstadoPostulacion(
    unittest.IsolatedAsyncioTestCase
):

    def crear_database(
        self,
        postulacion=None,
        modified_count=1,
    ):

        return SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(
                    return_value=postulacion
                ),
                update_one=AsyncMock(
                    return_value=SimpleNamespace(
                        modified_count=modified_count
                    )
                ),
            )
        )

    async def ejecutar_ruta(
        self,
        base,
        estado,
        usuario=USUARIO_AR,
        auditoria=None,
    ):

        if auditoria is None:
            auditoria = AsyncMock()

        with (
            patch.object(
                postulacion_route,
                "database",
                base,
            ),
            patch.object(
                postulacion_route,
                "client",
                FakeClient(),
            ),
            patch.object(
                postulacion_route,
                "registrar_auditoria",
                auditoria,
            ),
        ):

            resultado = await (
                postulacion_route.cambiar_estado_postulacion(
                    POSTULACION_ID,
                    CambiarEstadoPostulacionRequest(
                        estado=estado
                    ),
                    current_user=usuario,
                )
            )

        return resultado, auditoria

    # --------------------------------------------------
    # RECIBIDA -> EN REVISIÓN
    # --------------------------------------------------

    async def test_comenzar_revision_correctamente(self):

        postulacion = {
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
            "estado": "recibida",
        }

        base = self.crear_database(postulacion)

        resultado, auditoria = await self.ejecutar_ruta(
            base,
            "en_revision",
        )

        self.assertEqual(
            resultado["estado_anterior"],
            "recibida",
        )

        self.assertEqual(
            resultado["estado_nuevo"],
            "en_revision",
        )

        self.assertIsNotNone(
            resultado["fecha_actualizacion"],
        )

        base.postulaciones.update_one.assert_awaited_once_with(
            {
                "_id": ObjectId(POSTULACION_ID),
                "sello_id": "sello_01",
                "estado": "recibida",
            },
            {
                "$set": {
                    "estado": "en_revision",
                    "updated_at": ANY,
                }
            },
        )

        auditoria.assert_awaited_once_with(
            usuario=USUARIO_AR,
            sello_id="sello_01",
            postulacion_id=POSTULACION_ID,
            recurso="postulacion",
            recurso_id=POSTULACION_ID,
            accion="CAMBIO_ESTADO_POSTULACION",
            metodo="cambiar_estado",
            fecha_evento=ANY,
            estado_anterior="recibida",
            estado_nuevo="en_revision",
        )

    # --------------------------------------------------
    # EN REVISIÓN -> SELECCIONADA
    # --------------------------------------------------

    async def test_seleccionar_postulacion_correctamente(self):

        postulacion = {
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
            "estado": "en_revision",
        }

        base = self.crear_database(postulacion)

        resultado, auditoria = await self.ejecutar_ruta(
            base,
            "seleccionada",
        )

        self.assertEqual(
            resultado["estado_nuevo"],
            "seleccionada",
        )

        auditoria.assert_awaited_once_with(
            usuario=USUARIO_AR,
            sello_id="sello_01",
            postulacion_id=POSTULACION_ID,
            recurso="postulacion",
            recurso_id=POSTULACION_ID,
            accion="DECISION_FINAL_POSTULACION",
            metodo="cambiar_estado",
            estado_anterior="en_revision",
            estado_nuevo="seleccionada",
            fecha_evento=ANY,
        )

    # --------------------------------------------------
    # EN REVISIÓN -> DESCARTADA
    # --------------------------------------------------

    async def test_descartar_postulacion_correctamente(self):

        postulacion = {
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
            "estado": "en_revision",
        }

        base = self.crear_database(postulacion)

        resultado, auditoria = await self.ejecutar_ruta(
            base,
            "descartada",
        )

        self.assertEqual(
            resultado["estado_nuevo"],
            "descartada",
        )

        auditoria.assert_awaited_once_with(
            usuario=USUARIO_AR,
            sello_id="sello_01",
            postulacion_id=POSTULACION_ID,
            recurso="postulacion",
            recurso_id=POSTULACION_ID,
            accion="DECISION_FINAL_POSTULACION",
            metodo="cambiar_estado",
            estado_anterior="en_revision",
            estado_nuevo="descartada",
            fecha_evento=ANY,
        )

    # --------------------------------------------------
    # TRANSICIONES NO PERMITIDAS
    # --------------------------------------------------

    async def test_no_permitir_seleccionar_sin_revision(self):

        postulacion = {
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
            "estado": "recibida",
        }

        base = self.crear_database(postulacion)

        auditoria = AsyncMock()

        with self.assertRaises(HTTPException) as contexto:

            await self.ejecutar_ruta(
                base,
                "seleccionada",
                auditoria=auditoria,
            )

        self.assertEqual(
            contexto.exception.status_code,
            409,
        )

        base.postulaciones.update_one.assert_not_awaited()
        auditoria.assert_not_awaited()

    async def test_no_permitir_descartar_sin_revision(self):

        postulacion = {
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
            "estado": "recibida",
        }

        base = self.crear_database(postulacion)

        auditoria = AsyncMock()

        with self.assertRaises(HTTPException) as contexto:

            await self.ejecutar_ruta(
                base,
                "descartada",
                auditoria=auditoria,
            )

        self.assertEqual(
            contexto.exception.status_code,
            409,
        )

        base.postulaciones.update_one.assert_not_awaited()
        auditoria.assert_not_awaited()

    async def test_no_permitir_regresar_a_recibida(self):

        postulacion = {
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
            "estado": "en_revision",
        }

        base = self.crear_database(postulacion)

        auditoria = AsyncMock()

        with self.assertRaises(HTTPException) as contexto:

            await self.ejecutar_ruta(
                base,
                "recibida",
                auditoria=auditoria,
            )

        self.assertEqual(
            contexto.exception.status_code,
            409,
        )

        base.postulaciones.update_one.assert_not_awaited()
        auditoria.assert_not_awaited()

    async def test_no_permitir_cambiar_decision_final(self):

        postulacion = {
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
            "estado": "seleccionada",
        }

        base = self.crear_database(postulacion)

        auditoria = AsyncMock()

        with self.assertRaises(HTTPException) as contexto:

            await self.ejecutar_ruta(
                base,
                "descartada",
                auditoria=auditoria,
            )

        self.assertEqual(
            contexto.exception.status_code,
            409,
        )

        base.postulaciones.update_one.assert_not_awaited()
        auditoria.assert_not_awaited()

    # --------------------------------------------------
    # VALIDACIONES
    # --------------------------------------------------

    async def test_postulacion_no_encontrada(self):

        base = self.crear_database()

        auditoria = AsyncMock()

        with self.assertRaises(HTTPException) as contexto:

            await self.ejecutar_ruta(
                base,
                "en_revision",
                auditoria=auditoria,
            )

        self.assertEqual(
            contexto.exception.status_code,
            404,
        )

        auditoria.assert_not_awaited()

    async def test_rechazar_usuario_sin_rol_ar(self):

        base = self.crear_database()

        with self.assertRaises(HTTPException) as contexto:

            await self.ejecutar_ruta(
                base,
                "en_revision",
                usuario={
                    "_id": ObjectId(),
                    "role": "admin",
                    "label_id": "sello_01",
                },
            )

        self.assertEqual(
            contexto.exception.status_code,
            403,
        )

        base.postulaciones.find_one.assert_not_awaited()

    async def test_rechazar_usuario_sin_sello(self):

        base = self.crear_database()

        with self.assertRaises(HTTPException) as contexto:

            await self.ejecutar_ruta(
                base,
                "en_revision",
                usuario={
                    "_id": ObjectId(),
                    "role": "ar",
                    "label_id": None,
                },
            )

        self.assertEqual(
            contexto.exception.status_code,
            403,
        )

        base.postulaciones.find_one.assert_not_awaited()

    async def test_rechazar_id_invalido(self):

        base = self.crear_database()

        with self.assertRaises(HTTPException) as contexto:

            with (
                patch.object(
                    postulacion_route,
                    "database",
                    base,
                ),
                patch.object(
                    postulacion_route,
                    "client",
                    FakeClient(),
                ),
            ):

                await (
                    postulacion_route.cambiar_estado_postulacion(
                        "id-invalido",
                        CambiarEstadoPostulacionRequest(
                            estado="en_revision"
                        ),
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            400,
        )

        base.postulaciones.find_one.assert_not_awaited()

    async def test_rechazar_estado_no_permitido_por_esquema(self):

        with self.assertRaises(ValidationError):

            CambiarEstadoPostulacionRequest(
                estado="en_espera"
            )

    # --------------------------------------------------
    # CONCURRENCIA Y AUDITORÍA
    # --------------------------------------------------

    async def test_rechazar_actualizacion_concurrente(self):

        postulacion = {
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
            "estado": "recibida",
        }

        base = self.crear_database(
            postulacion,
            modified_count=0,
        )

        auditoria = AsyncMock()

        with self.assertRaises(HTTPException) as contexto:

            await self.ejecutar_ruta(
                base,
                "en_revision",
                auditoria=auditoria,
            )

        self.assertEqual(
            contexto.exception.status_code,
            409,
        )

        auditoria.assert_not_awaited()

    async def test_error_al_registrar_auditoria(self):

        postulacion = {
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
            "estado": "recibida",
        }

        base = self.crear_database(postulacion)

        auditoria = AsyncMock(
            side_effect=RuntimeError(
                "Error simulado de auditoría."
            )
        )

        with self.assertRaises(HTTPException) as contexto:

            await self.ejecutar_ruta(
                base,
                "en_revision",
                auditoria=auditoria,
            )

        self.assertEqual(
            contexto.exception.status_code,
            500,
        )


if __name__ == "__main__":
    unittest.main()
