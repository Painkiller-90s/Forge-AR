
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.routes import evaluacion_route


POSTULACION_ID = "6af89461a49fdfdae7b24da4"

USUARIO_AR = {
    "_id": ObjectId("6af89461a49fdfdae7b24da6"),
    "role": "ar",
    "label_id": "sello_01",
}


class SesionTransaccionalFalsa:
    """Simula el comportamiento básico de with_transaction."""

    def __init__(self):
        self.committed = False
        self.aborted = False
        self.callback_calls = 0

    async def with_transaction(self, callback):
        self.callback_calls += 1

        try:
            resultado = await callback(self)

        except Exception:
            self.aborted = True
            raise

        self.committed = True
        return resultado


class ContextoSesionFalso:

    def __init__(self, session):
        self.session = session
        self.activo = False
        self.ingresado = False
        self.salido = False

    async def __aenter__(self):
        self.activo = True
        self.ingresado = True
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        self.activo = False
        self.salido = True
        return False


class TestHU009EvaluacionRoute(
    unittest.IsolatedAsyncioTestCase
):

    def crear_evaluacion(self):
        return {
            "postulacion_id": POSTULACION_ID,
            "viabilidad": {
                "estado": "evaluable",
                "score": 80.5,
                "nivel_riesgo": "bajo",
                "dimensiones": {
                    "q_audio": 85,
                    "q_streaming": {
                        "q_streaming": 100
                    },
                    "q_rrss": {
                        "q_rrss": 40
                    },
                    "q_presskit": {
                        "q_presskit": 70
                    },
                    "q_consistencia": {
                        "q_consistencia": 100
                    },
                },
                "aportes": {},
                "dimensiones_faltantes": [],
                "motivos_no_evaluable": [],
            },
            "fuentes": {
                "spotify": {
                    "disponible": True
                },
                "lastfm": {
                    "disponible": True,
                    "identidad_confirmada": True,
                },
                "instagram": {
                    "disponible": True
                },
            },
            "datos_utilizados": {
                "press_kit": {},
                "demos": [],
                "spotify": {},
                "lastfm": {},
                "instagram": {},
            },
        }

    def crear_database(self, error_insert=None):

        insert_one = AsyncMock()

        if error_insert:
            insert_one.side_effect = error_insert

        return SimpleNamespace(
            evaluaciones=SimpleNamespace(
                insert_one=insert_one,
            )
        )

    def crear_cliente(self):

        session = SesionTransaccionalFalsa()

        contexto = ContextoSesionFalso(session)

        bind = Mock(
            return_value=contexto
        )

        start_session = Mock(
            return_value=SimpleNamespace(
                bind=bind
            )
        )

        cliente = SimpleNamespace(
            start_session=start_session
        )

        return cliente, session, contexto, start_session, bind

    async def test_generar_reporte_correctamente(self):

        base = self.crear_database()

        cliente, session, contexto, start_session, bind = (
            self.crear_cliente()
        )

        evaluacion = self.crear_evaluacion()

        generar = AsyncMock(
            return_value=evaluacion
        )

        auditoria = AsyncMock()

        with (
            patch.object(
                evaluacion_route,
                "database",
                base,
            ),
            patch.object(
                evaluacion_route,
                "client",
                cliente,
            ),
            patch.object(
                evaluacion_route,
                "generar_evaluacion_actual",
                generar,
            ),
            patch.object(
                evaluacion_route,
                "registrar_auditoria",
                auditoria,
            ),
        ):

            resultado = await (
                evaluacion_route.generar_reporte_evaluacion(
                    POSTULACION_ID,
                    current_user=USUARIO_AR,
                )
            )

        documento = (
            base.evaluaciones.insert_one.await_args.args[0]
        )

        evaluacion_id = str(documento["_id"])

        self.assertEqual(
            resultado["evaluacion_id"],
            evaluacion_id,
        )

        self.assertEqual(
            resultado["postulacion_id"],
            POSTULACION_ID,
        )

        self.assertEqual(
            resultado["estado"],
            "evaluable",
        )

        self.assertEqual(
            resultado["viabilidad"]["score"],
            80.5,
        )

        self.assertEqual(
            documento["sello_id"],
            "sello_01",
        )

        self.assertEqual(
            documento["evaluador_id"],
            str(USUARIO_AR["_id"]),
        )

        self.assertIsInstance(
            documento["fecha_generacion"],
            datetime,
        )

        generar.assert_awaited_once_with(
            postulacion_id=POSTULACION_ID,
            sello_id="sello_01",
        )

        auditoria.assert_awaited_once()

        self.assertEqual(
            auditoria.await_args.kwargs["accion"],
            "GENERACION_EVALUACION",
        )

        self.assertEqual(
            auditoria.await_args.kwargs["recurso_id"],
            evaluacion_id,
        )

        # Verificar el uso de la sesión transaccional.
        start_session.assert_called_once_with()
        bind.assert_called_once_with()

        self.assertTrue(session.committed)
        self.assertFalse(session.aborted)

        self.assertEqual(
            session.callback_calls,
            1,
        )

        self.assertTrue(contexto.ingresado)
        self.assertTrue(contexto.salido)

    async def test_rechazar_usuario_sin_rol_ar(self):

        generar = AsyncMock()

        with patch.object(
            evaluacion_route,
            "generar_evaluacion_actual",
            generar,
        ):

            with self.assertRaises(HTTPException) as contexto:

                await (
                    evaluacion_route.generar_reporte_evaluacion(
                        POSTULACION_ID,
                        current_user={
                            "_id": ObjectId(),
                            "role": "admin",
                            "label_id": "sello_01",
                        },
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            403,
        )

        generar.assert_not_awaited()

    async def test_rechazar_usuario_sin_sello(self):

        generar = AsyncMock()

        with patch.object(
            evaluacion_route,
            "generar_evaluacion_actual",
            generar,
        ):

            with self.assertRaises(HTTPException) as contexto:

                await (
                    evaluacion_route.generar_reporte_evaluacion(
                        POSTULACION_ID,
                        current_user={
                            "_id": ObjectId(),
                            "role": "ar",
                        },
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            403,
        )

        generar.assert_not_awaited()

    async def test_rechazar_id_invalido(self):

        generar = AsyncMock()

        with patch.object(
            evaluacion_route,
            "generar_evaluacion_actual",
            generar,
        ):

            with self.assertRaises(HTTPException) as contexto:

                await (
                    evaluacion_route.generar_reporte_evaluacion(
                        "id-invalido",
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(
            contexto.exception.status_code,
            400,
        )

        generar.assert_not_awaited()

    async def test_postulacion_no_encontrada(self):

        base = self.crear_database()

        generar = AsyncMock(
            return_value=None
        )

        cliente, session, contexto, start_session, bind = (
            self.crear_cliente()
        )

        with (
            patch.object(
                evaluacion_route,
                "database",
                base,
            ),
            patch.object(
                evaluacion_route,
                "client",
                cliente,
            ),
            patch.object(
                evaluacion_route,
                "generar_evaluacion_actual",
                generar,
            ),
        ):

            with self.assertRaises(HTTPException) as contexto_error:

                await (
                    evaluacion_route.generar_reporte_evaluacion(
                        POSTULACION_ID,
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(
            contexto_error.exception.status_code,
            404,
        )

        base.evaluaciones.insert_one.assert_not_awaited()

        start_session.assert_not_called()

    async def test_error_al_calcular_evaluacion(self):

        base = self.crear_database()

        generar = AsyncMock(
            side_effect=ValueError("Datos incompatibles")
        )

        cliente, session, contexto, start_session, bind = (
            self.crear_cliente()
        )

        with (
            patch.object(
                evaluacion_route,
                "database",
                base,
            ),
            patch.object(
                evaluacion_route,
                "client",
                cliente,
            ),
            patch.object(
                evaluacion_route,
                "generar_evaluacion_actual",
                generar,
            ),
        ):

            with self.assertRaises(HTTPException) as contexto_error:

                await (
                    evaluacion_route.generar_reporte_evaluacion(
                        POSTULACION_ID,
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(
            contexto_error.exception.status_code,
            500,
        )

        base.evaluaciones.insert_one.assert_not_awaited()

        start_session.assert_not_called()

    async def test_error_al_guardar_reporte(self):

        base = self.crear_database(
            error_insert=RuntimeError("MongoDB no disponible")
        )

        cliente, session, contexto, start_session, bind = (
            self.crear_cliente()
        )

        generar = AsyncMock(
            return_value=self.crear_evaluacion()
        )

        auditoria = AsyncMock()

        with (
            patch.object(
                evaluacion_route,
                "database",
                base,
            ),
            patch.object(
                evaluacion_route,
                "client",
                cliente,
            ),
            patch.object(
                evaluacion_route,
                "generar_evaluacion_actual",
                generar,
            ),
            patch.object(
                evaluacion_route,
                "registrar_auditoria",
                auditoria,
            ),
        ):

            with self.assertRaises(HTTPException) as contexto_error:

                await (
                    evaluacion_route.generar_reporte_evaluacion(
                        POSTULACION_ID,
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(
            contexto_error.exception.status_code,
            500,
        )

        base.evaluaciones.insert_one.assert_awaited_once()

        auditoria.assert_not_awaited()

        self.assertTrue(session.aborted)
        self.assertFalse(session.committed)

        self.assertTrue(contexto.salido)

    async def test_error_al_registrar_auditoria(self):

        base = self.crear_database()

        cliente, session, contexto, start_session, bind = (
            self.crear_cliente()
        )

        generar = AsyncMock(
            return_value=self.crear_evaluacion()
        )

        auditoria = AsyncMock(
            side_effect=RuntimeError("Error de auditoría")
        )

        with (
            patch.object(
                evaluacion_route,
                "database",
                base,
            ),
            patch.object(
                evaluacion_route,
                "client",
                cliente,
            ),
            patch.object(
                evaluacion_route,
                "generar_evaluacion_actual",
                generar,
            ),
            patch.object(
                evaluacion_route,
                "registrar_auditoria",
                auditoria,
            ),
        ):

            with self.assertRaises(HTTPException) as contexto_error:

                await (
                    evaluacion_route.generar_reporte_evaluacion(
                        POSTULACION_ID,
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(
            contexto_error.exception.status_code,
            500,
        )

        # Ambas operaciones se ejecutaron dentro
        # del flujo transaccional simulado.
        base.evaluaciones.insert_one.assert_awaited_once()
        auditoria.assert_awaited_once()

        # La transacción debe abortarse ante el error.
        self.assertTrue(session.aborted)
        self.assertFalse(session.committed)

        self.assertTrue(contexto.salido)


if __name__ == "__main__":
    unittest.main()
