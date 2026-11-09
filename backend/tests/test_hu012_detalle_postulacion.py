
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app
from app.routes import postulacion_route
from app.routes.auth_route import get_current_user


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"
FECHA = datetime(2026, 11, 7, tzinfo=timezone.utc)


def crear_postulacion():
    return {
        "_id": ObjectId(POSTULACION_ID),
        "sello_id": "sello_01",
        "press_kit": {
            "nombre_artistico": "Neurosis",
            "correo_contacto": "contacto@neurosis.com",
            "pais": "Estados Unidos",
            "ciudad": "San Francisco",
            "tipo_proyecto": "Banda",
            "generos": ["Post-Metal", "Sludge Metal"],
            "integrantes": ["Integrante 1", "Integrante 2"],
            "biografia": "Banda de prueba para validar HU012.",
            "anio_inicio": 1985,
            "spotify_url": "https://open.spotify.com/artist/123",
            "instagram_url": "https://www.instagram.com/neurosis",
            "mensaje_sello": "Presentación de prueba.",
        },
        "demos": [
            {
                "archivo_id": "demo_123",
                "nombre": "Canción de prueba",
                "nombre_archivo": "demo.flac",
                "formato": "flac",
                "tamano_bytes": 68595303,
                "mime_type": "audio/flac",
                "sha256": "a" * 64,
                "storage_key": "privado/sello_01/demo.flac",
                "uploaded_at": FECHA,
                "audio_tecnico": {
                    "codec": "flac",
                    "formato_contenedor": "flac",
                    "sample_rate_hz": 44100,
                    "bitrate_bps": 865734,
                    "bits_per_sample": 16,
                    "channels": 2,
                    "duracion_segundos": 633.8,
                },
                "validacion_tecnica": {
                    "valido": True,
                    "motivos_rechazo": [],
                    "q_audio": 93,
                },
            }
        ],
        "estado": "recibida",
        "created_at": FECHA,
        "updated_at": FECHA,
    }


class TestHU012DetallePostulacion(unittest.TestCase):

    def setUp(self):
        self.usuario = {
            "_id": ObjectId(),
            "role": "ar",
            "label_id": "sello_01",
        }

        self.overrides_originales = (
            app.dependency_overrides.copy()
        )

        app.dependency_overrides[get_current_user] = (
            lambda: self.usuario
        )

        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

        app.dependency_overrides.clear()
        app.dependency_overrides.update(
            self.overrides_originales
        )

    def preparar_database(self, documento):
        coleccion = SimpleNamespace(
            find_one=AsyncMock(return_value=documento)
        )

        database = SimpleNamespace(
            postulaciones=coleccion
        )

        parche = patch.object(
            postulacion_route,
            "database",
            database,
        )

        parche.start()
        self.addCleanup(parche.stop)

        return coleccion

    def preparar_auditoria(self, fallo=False):
        side_effect = (
            RuntimeError("Error de auditoría")
            if fallo else None
        )

        auditoria = AsyncMock(
            side_effect=side_effect
        )

        parche = patch.object(
            postulacion_route,
            "registrar_auditoria",
            new=auditoria,
        )

        parche.start()
        self.addCleanup(parche.stop)

        return auditoria

    def test_consultar_detalle_autorizado(self):
        coleccion = self.preparar_database(
            crear_postulacion()
        )

        auditoria = self.preparar_auditoria()

        respuesta = self.client.get(
            f"/postulaciones/{POSTULACION_ID}"
        )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.json()

        self.assertEqual(
            datos["press_kit"]["nombre_artistico"],
            "Neurosis",
        )

        self.assertEqual(
            datos["press_kit"]["generos"],
            ["Post-Metal", "Sludge Metal"],
        )

        self.assertEqual(
            datos["demos"][0]["audio_tecnico"]["codec"],
            "flac",
        )

        self.assertEqual(
            datos["demos"][0]["validacion_tecnica"]["q_audio"],
            93,
        )

        # No exponer la clave interna de R2.
        self.assertNotIn(
            "storage_key",
            datos["demos"][0],
        )

        coleccion.find_one.assert_awaited_once_with({
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
        })

        auditoria.assert_awaited_once()

        llamada = auditoria.await_args.kwargs

        self.assertEqual(
            llamada["accion"],
            "CONSULTA_POSTULACION",
        )

        self.assertEqual(
            llamada["recurso"],
            "postulacion",
        )

    def test_rechazar_usuario_sin_rol_ar(self):
        coleccion = self.preparar_database(
            crear_postulacion()
        )

        auditoria = self.preparar_auditoria()

        self.usuario["role"] = "artista"

        respuesta = self.client.get(
            f"/postulaciones/{POSTULACION_ID}"
        )

        self.assertEqual(respuesta.status_code, 403)

        coleccion.find_one.assert_not_awaited()
        auditoria.assert_not_awaited()

    def test_rechazar_usuario_sin_sello(self):
        coleccion = self.preparar_database(
            crear_postulacion()
        )

        auditoria = self.preparar_auditoria()

        self.usuario["label_id"] = None

        respuesta = self.client.get(
            f"/postulaciones/{POSTULACION_ID}"
        )

        self.assertEqual(respuesta.status_code, 403)

        coleccion.find_one.assert_not_awaited()
        auditoria.assert_not_awaited()

    def test_rechazar_id_invalido(self):
        coleccion = self.preparar_database(None)

        auditoria = self.preparar_auditoria()

        respuesta = self.client.get(
            "/postulaciones/id-invalido"
        )

        self.assertEqual(respuesta.status_code, 400)

        coleccion.find_one.assert_not_awaited()
        auditoria.assert_not_awaited()

    def test_aislamiento_por_sello(self):
        coleccion = self.preparar_database(None)

        auditoria = self.preparar_auditoria()

        respuesta = self.client.get(
            f"/postulaciones/{POSTULACION_ID}"
        )

        self.assertEqual(respuesta.status_code, 404)

        coleccion.find_one.assert_awaited_once_with({
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
        })

        auditoria.assert_not_awaited()

    def test_fallo_al_registrar_auditoria(self):
        self.preparar_database(crear_postulacion())

        auditoria = self.preparar_auditoria(
            fallo=True
        )

        respuesta = self.client.get(
            f"/postulaciones/{POSTULACION_ID}"
        )

        self.assertEqual(respuesta.status_code, 500)

        self.assertEqual(
            respuesta.json()["detail"],
            "No fue posible registrar la consulta.",
        )

        auditoria.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
