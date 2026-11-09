
import io
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app
from app.routes import postulacion_route
from app.routes.auth_route import get_current_user
from app.utils.security import (
    create_access_token,
    decode_access_token,
)


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"
ARCHIVO_ID = "demo_123"


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
            "integrantes": ["Integrante 1"],
            "biografia": "Banda de prueba para HU012.",
            "anio_inicio": 1985,
            "spotify_url": None,
            "instagram_url": None,
            "mensaje_sello": None,
        },
        "demos": [
            {
                "archivo_id": ARCHIVO_ID,
                "nombre": "Canción de prueba",
                "nombre_archivo": "demo.flac",
                "formato": "flac",
                "tamano_bytes": 10,
                "mime_type": "audio/flac",
                "sha256": "a" * 64,
                "storage_key": "privado/sello_01/demo.flac",
                "uploaded_at": None,
                "audio_tecnico": None,
                "validacion_tecnica": {
                    "valido": True,
                    "motivos_rechazo": [],
                    "q_audio": 93,
                },
            }
        ],
        "estado": "recibida",
    }


class TestHU012ReproduccionDemo(unittest.TestCase):

    def setUp(self):
        self.usuario = {
            "_id": ObjectId(),
            "role": "ar",
            "label_id": "sello_01",
            "is_active": True,
        }

        self.overrides_originales = (
            app.dependency_overrides.copy()
        )

        app.dependency_overrides[get_current_user] = (
            lambda: self.usuario
        )

        self.client = TestClient(app)

        self.ruta_token = (
            f"/postulaciones/{POSTULACION_ID}"
            f"/demos/{ARCHIVO_ID}/playback-token"
        )

        self.ruta_stream = (
            f"/postulaciones/{POSTULACION_ID}"
            f"/demos/{ARCHIVO_ID}/stream"
        )

    def tearDown(self):
        self.client.close()

        app.dependency_overrides.clear()
        app.dependency_overrides.update(
            self.overrides_originales
        )

    def preparar_database(
        self,
        postulacion=None,
        usuario=None,
    ):
        usuarios = SimpleNamespace(
            find_one=AsyncMock(return_value=usuario)
        )

        postulaciones = SimpleNamespace(
            find_one=AsyncMock(return_value=postulacion)
        )

        database_mock = SimpleNamespace(
            users=usuarios,
            postulaciones=postulaciones,
        )

        parche = patch.object(
            postulacion_route,
            "database",
            database_mock,
        )

        parche.start()
        self.addCleanup(parche.stop)

        return usuarios, postulaciones

    def crear_token(
        self,
        expires_delta=None,
        **cambios,
    ):
        payload = {
            "uid": str(self.usuario["_id"]),
            "purpose": "demo_stream",
            "sello_id": "sello_01",
            "postulacion_id": POSTULACION_ID,
            "archivo_id": ARCHIVO_ID,
        }

        payload.update(cambios)

        if expires_delta is None:
            expires_delta = timedelta(minutes=30)

        return create_access_token(
            payload,
            expires_delta=expires_delta,
        )

    def preparar_streaming(
        self,
        postulacion=None,
        usuario=None,
        cuerpo=None,
        auditoria=None,
    ):
        if postulacion is None:
            postulacion = crear_postulacion()

        if usuario is None:
            usuario = self.usuario

        usuarios, postulaciones = self.preparar_database(
            postulacion,
            usuario,
        )

        if cuerpo is None:
            cuerpo = io.BytesIO(b"audio-demo")

        objeto = {
            "Body": cuerpo,
            "ContentLength": len(cuerpo.getvalue()),
        }

        obtener = AsyncMock(return_value=objeto)

        if auditoria is None:
            auditoria = AsyncMock()

        parche_r2 = patch.object(
            postulacion_route,
            "obtener_demo_privada",
            new=obtener,
        )

        parche_auditoria = patch.object(
            postulacion_route,
            "registrar_auditoria",
            new=auditoria,
        )

        parche_r2.start()
        parche_auditoria.start()

        self.addCleanup(parche_r2.stop)
        self.addCleanup(parche_auditoria.stop)

        return (
            usuarios,
            postulaciones,
            obtener,
            auditoria,
            cuerpo,
        )

    # =====================================
    # GENERACION DEL TOKEN
    # =====================================

    def test_generar_token_autorizado(self):
        self.preparar_database(
            crear_postulacion(),
            self.usuario,
        )

        respuesta = self.client.post(
            self.ruta_token
        )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.json()

        self.assertEqual(datos["token_type"], "Bearer")
        self.assertEqual(datos["expires_in"], 1800)

        payload = decode_access_token(datos["token"])

        self.assertEqual(
            payload["uid"],
            str(self.usuario["_id"]),
        )

        self.assertEqual(
            payload["purpose"],
            "demo_stream",
        )

        self.assertEqual(
            payload["sello_id"],
            "sello_01",
        )

        self.assertEqual(
            payload["postulacion_id"],
            POSTULACION_ID,
        )

        self.assertEqual(
            payload["archivo_id"],
            ARCHIVO_ID,
        )

    def test_rechazar_generacion_sin_rol_ar(self):
        self.usuario["role"] = "artista"

        _, postulaciones = self.preparar_database(
            crear_postulacion(),
            self.usuario,
        )

        respuesta = self.client.post(
            self.ruta_token
        )

        self.assertEqual(respuesta.status_code, 403)
        postulaciones.find_one.assert_not_awaited()

    def test_rechazar_generacion_sin_sello(self):
        self.usuario["label_id"] = None

        _, postulaciones = self.preparar_database(
            crear_postulacion(),
            self.usuario,
        )

        respuesta = self.client.post(
            self.ruta_token
        )

        self.assertEqual(respuesta.status_code, 403)
        postulaciones.find_one.assert_not_awaited()

    def test_rechazar_id_postulacion_invalido(self):
        _, postulaciones = self.preparar_database(
            crear_postulacion(),
            self.usuario,
        )

        respuesta = self.client.post(
            "/postulaciones/id-invalido"
            f"/demos/{ARCHIVO_ID}/playback-token"
        )

        self.assertEqual(respuesta.status_code, 400)
        postulaciones.find_one.assert_not_awaited()

    def test_rechazar_postulacion_de_otro_sello(self):
        _, postulaciones = self.preparar_database(
            None,
            self.usuario,
        )

        respuesta = self.client.post(
            self.ruta_token
        )

        self.assertEqual(respuesta.status_code, 404)

        postulaciones.find_one.assert_awaited_once_with({
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
        })

    def test_rechazar_demo_inexistente_al_generar_token(self):
        postulacion = crear_postulacion()
        postulacion["demos"] = []

        self.preparar_database(
            postulacion,
            self.usuario,
        )

        respuesta = self.client.post(
            self.ruta_token
        )

        self.assertEqual(respuesta.status_code, 404)

    # =====================================
    # VALIDACION DEL TOKEN DE REPRODUCCION
    # =====================================

    def test_rechazar_token_invalido(self):
        usuarios, postulaciones = self.preparar_database(
            crear_postulacion(),
            self.usuario,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": "token-invalido"},
        )

        self.assertEqual(respuesta.status_code, 401)

        usuarios.find_one.assert_not_awaited()
        postulaciones.find_one.assert_not_awaited()

    def test_rechazar_token_expirado(self):
        token = self.crear_token(
            expires_delta=timedelta(seconds=-1)
        )

        usuarios, postulaciones = self.preparar_database(
            crear_postulacion(),
            self.usuario,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": token},
        )

        self.assertEqual(respuesta.status_code, 401)

        usuarios.find_one.assert_not_awaited()
        postulaciones.find_one.assert_not_awaited()

    def test_rechazar_token_de_otra_postulacion_o_demo(self):
        usuarios, postulaciones = self.preparar_database(
            crear_postulacion(),
            self.usuario,
        )

        casos = [
            {"postulacion_id": "otra_postulacion"},
            {"archivo_id": "otra_demo"},
            {"purpose": "otro_proposito"},
        ]

        for cambios in casos:
            with self.subTest(cambios=cambios):
                token = self.crear_token(**cambios)

                respuesta = self.client.get(
                    self.ruta_stream,
                    params={"token": token},
                )

                self.assertEqual(
                    respuesta.status_code,
                    401,
                )

        usuarios.find_one.assert_not_awaited()
        postulaciones.find_one.assert_not_awaited()

    # =====================================
    # VALIDACION DEL USUARIO
    # =====================================

    def test_rechazar_usuario_inexistente(self):
        usuarios, postulaciones = self.preparar_database(
            crear_postulacion(),
            None,
        )

        token = self.crear_token()

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": token},
        )

        self.assertEqual(respuesta.status_code, 401)

        usuarios.find_one.assert_awaited_once()
        postulaciones.find_one.assert_not_awaited()

    def test_rechazar_usuario_desactivado(self):
        usuario = self.usuario.copy()
        usuario["is_active"] = False

        usuarios, postulaciones = self.preparar_database(
            crear_postulacion(),
            usuario,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": self.crear_token()},
        )

        self.assertEqual(respuesta.status_code, 403)
        postulaciones.find_one.assert_not_awaited()

    def test_rechazar_usuario_sin_rol_ar(self):
        usuario = self.usuario.copy()
        usuario["role"] = "artista"

        _, postulaciones = self.preparar_database(
            crear_postulacion(),
            usuario,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": self.crear_token()},
        )

        self.assertEqual(respuesta.status_code, 403)
        postulaciones.find_one.assert_not_awaited()

    def test_rechazar_usuario_de_otro_sello(self):
        usuario = self.usuario.copy()
        usuario["label_id"] = "sello_02"

        _, postulaciones = self.preparar_database(
            crear_postulacion(),
            usuario,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": self.crear_token()},
        )

        self.assertEqual(respuesta.status_code, 403)
        postulaciones.find_one.assert_not_awaited()

    # =====================================
    # VALIDACION DE POSTULACION Y DEMO
    # =====================================

    def test_rechazar_postulacion_no_encontrada(self):
        _, postulaciones = self.preparar_database(
            None,
            self.usuario,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": self.crear_token()},
        )

        self.assertEqual(respuesta.status_code, 404)

        postulaciones.find_one.assert_awaited_once_with({
            "_id": ObjectId(POSTULACION_ID),
            "sello_id": "sello_01",
        })

    def test_rechazar_demo_no_encontrada(self):
        postulacion = crear_postulacion()
        postulacion["demos"] = []

        _, postulaciones = self.preparar_database(
            postulacion,
            self.usuario,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": self.crear_token()},
        )

        self.assertEqual(respuesta.status_code, 404)
        postulaciones.find_one.assert_awaited_once()

    # =====================================
    # STREAMING DE AUDIO
    # =====================================

    def test_reproduccion_autorizada(self):
        (
            usuarios,
            postulaciones,
            obtener,
            auditoria,
            cuerpo,
        ) = self.preparar_streaming()

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": self.crear_token()},
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.content,
            b"audio-demo",
        )

        self.assertEqual(
            respuesta.headers["content-type"],
            "audio/flac",
        )

        self.assertEqual(
            respuesta.headers["accept-ranges"],
            "bytes",
        )

        self.assertEqual(
            respuesta.headers["cache-control"],
            "no-store",
        )

        obtener.assert_awaited_once_with(
            "privado/sello_01/demo.flac",
            None,
        )

        usuarios.find_one.assert_awaited_once()
        postulaciones.find_one.assert_awaited_once()

        auditoria.assert_awaited_once()

        llamada = auditoria.await_args.kwargs

        self.assertEqual(
            llamada["accion"],
            "ACCESO_DEMO_AUTORIZADO",
        )

        self.assertEqual(
            llamada["recurso"],
            "demo",
        )

        self.assertEqual(
            llamada["metodo"],
            "stream",
        )

        self.assertTrue(cuerpo.closed)

    def test_reproduccion_con_rango_http(self):
        audio = b"0123456789"

        postulacion = crear_postulacion()
        postulacion["demos"][0]["tamano_bytes"] = len(audio)

        cuerpo = io.BytesIO(audio[2:6])

        (
            usuarios,
            postulaciones,
            obtener,
            auditoria,
            _,
        ) = self.preparar_streaming(
            postulacion=postulacion,
            cuerpo=cuerpo,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": self.crear_token()},
            headers={"Range": "bytes=2-5"},
        )

        self.assertEqual(respuesta.status_code, 206)
        self.assertEqual(respuesta.content, b"2345")

        self.assertEqual(
            respuesta.headers["content-range"],
            "bytes 2-5/10",
        )

        self.assertEqual(
            respuesta.headers["content-length"],
            "4",
        )

        obtener.assert_awaited_once_with(
            "privado/sello_01/demo.flac",
            "bytes=2-5",
        )

        auditoria.assert_awaited_once()

    def test_rechazar_rango_http_invalido(self):
        postulacion = crear_postulacion()
        postulacion["demos"][0]["tamano_bytes"] = 10

        (
            usuarios,
            postulaciones,
            obtener,
            auditoria,
            _,
        ) = self.preparar_streaming(
            postulacion=postulacion,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": self.crear_token()},
            headers={"Range": "bytes=10-"},
        )

        self.assertEqual(respuesta.status_code, 416)

        self.assertEqual(
            respuesta.headers["content-range"],
            "bytes */10",
        )

        obtener.assert_not_awaited()
        auditoria.assert_not_awaited()

    # =====================================
    # ERRORES DE ALMACENAMIENTO Y AUDITORIA
    # =====================================

    def test_error_al_obtener_audio_desde_r2(self):
        usuarios, postulaciones = self.preparar_database(
            crear_postulacion(),
            self.usuario,
        )

        obtener = AsyncMock(
            side_effect=RuntimeError("Error de R2")
        )

        auditoria = AsyncMock()

        with patch.object(
            postulacion_route,
            "obtener_demo_privada",
            new=obtener,
        ):
            with patch.object(
                postulacion_route,
                "registrar_auditoria",
                new=auditoria,
            ):
                respuesta = self.client.get(
                    self.ruta_stream,
                    params={"token": self.crear_token()},
                )

        self.assertEqual(respuesta.status_code, 502)

        obtener.assert_awaited_once()
        auditoria.assert_not_awaited()

    def test_fallo_auditoria_cierra_stream(self):
        cuerpo = io.BytesIO(b"audio-demo")

        auditoria = AsyncMock(
            side_effect=RuntimeError("Error de auditoria")
        )

        (
            usuarios,
            postulaciones,
            obtener,
            auditoria,
            cuerpo,
        ) = self.preparar_streaming(
            cuerpo=cuerpo,
            auditoria=auditoria,
        )

        respuesta = self.client.get(
            self.ruta_stream,
            params={"token": self.crear_token()},
        )

        self.assertEqual(respuesta.status_code, 500)

        self.assertEqual(
            respuesta.json()["detail"],
            "No fue posible registrar el acceso.",
        )

        auditoria.assert_awaited_once()
        obtener.assert_awaited_once()

        self.assertTrue(cuerpo.closed)


if __name__ == "__main__":
    unittest.main()
