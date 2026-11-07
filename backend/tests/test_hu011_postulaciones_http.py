
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app
from app.routes import postulacion_route
from app.routes.auth_route import get_current_user


FECHA = datetime(2026, 11, 7, tzinfo=timezone.utc)


def crear_postulacion(nombre, generos):
    return {
        "_id": ObjectId(),
        "sello_id": "sello_01",
        "press_kit": {
            "nombre_artistico": nombre,
            "pais": "Chile",
            "ciudad": "Santiago",
            "tipo_proyecto": "Banda",
            "generos": generos,
        },
        "estado": "recibida",
        "created_at": FECHA,
    }


def crear_database_simulada(documentos):
    cursor = Mock()
    cursor.sort.return_value = cursor
    cursor.to_list = AsyncMock(return_value=documentos)

    coleccion = SimpleNamespace(
        find=Mock(return_value=cursor)
    )

    database = SimpleNamespace(
        postulaciones=coleccion
    )

    return database, coleccion, cursor


class TestHU011PostulacionesHTTP(unittest.TestCase):

    def setUp(self):
        self.usuario = {
            "role": "ar",
            "label_id": "sello_01",
        }

        self.overrides_originales = app.dependency_overrides.copy()

        app.dependency_overrides[get_current_user] = (
            lambda: self.usuario
        )

        # No utilizar el context manager de TestClient:
        # evitamos ejecutar el lifespan y conectar MongoDB real.
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

        app.dependency_overrides.clear()
        app.dependency_overrides.update(
            self.overrides_originales
        )

    def preparar_database(self, documentos):
        database, coleccion, cursor = crear_database_simulada(
            documentos
        )

        parche = patch.object(
            postulacion_route,
            "database",
            database,
        )

        parche.start()
        self.addCleanup(parche.stop)

        return coleccion, cursor

    def preparar_generos_disponibles(self):
        mock = AsyncMock(
            return_value=["Metal", "Rock"]
        )

        parche = patch.object(
            postulacion_route,
            "obtener_generos_sello",
            new=mock,
        )

        parche.start()
        self.addCleanup(parche.stop)

        return mock

    async def dummy_placeholder(self):
        pass

    def test_listar_postulaciones_autorizadas(self):
        documentos = [
            crear_postulacion(
                "Artista A",
                ["Rock"],
            ),
            crear_postulacion(
                "Artista B",
                ["Metal"],
            ),
        ]

        coleccion, cursor = self.preparar_database(
            documentos
        )

        obtener_generos = self.preparar_generos_disponibles()

        respuesta = self.client.get(
            "/postulaciones/bandeja"
        )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.json()

        self.assertEqual(datos["total"], 2)
        self.assertEqual(len(datos["postulaciones"]), 2)

        self.assertEqual(
            datos["generos_disponibles"],
            ["Metal", "Rock"],
        )

        self.assertEqual(
            datos["postulaciones"][0]["nombre_artistico"],
            "Artista A",
        )

        coleccion.find.assert_called_once_with({
            "sello_id": "sello_01",
        })

        cursor.sort.assert_called_once_with(
            "created_at",
            -1,
        )

        obtener_generos.assert_awaited_once_with(
            "sello_01"
        )

    def test_filtro_multiple_generos_or(self):
        documentos = [
            crear_postulacion(
                "Artista Rock",
                ["Rock"],
            ),
            crear_postulacion(
                "Artista Metal",
                ["Metal"],
            ),
        ]

        coleccion, _ = self.preparar_database(
            documentos
        )

        self.preparar_generos_disponibles()

        normalizar = AsyncMock(
            return_value=["Rock", "Metal"]
        )

        with patch.object(
            postulacion_route,
            "normalizar_generos_sello",
            new=normalizar,
        ):
            respuesta = self.client.get(
                "/postulaciones/bandeja",
                params=[
                    ("generos", "rock"),
                    ("generos", "METAL"),
                ],
            )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.json()

        self.assertEqual(datos["total"], 2)

        normalizar.assert_awaited_once_with(
            ["rock", "METAL"],
            "sello_01",
        )

        coleccion.find.assert_called_once_with({
            "sello_id": "sello_01",
            "press_kit.generos": {
                "$in": ["Rock", "Metal"],
            },
        })

    def test_rechazar_usuario_sin_rol_ar(self):
        coleccion, _ = self.preparar_database([])

        self.usuario = {
            "role": "artista",
            "label_id": "sello_01",
        }

        respuesta = self.client.get(
            "/postulaciones/bandeja"
        )

        self.assertEqual(respuesta.status_code, 403)

        coleccion.find.assert_not_called()

    def test_rechazar_usuario_sin_sello(self):
        coleccion, _ = self.preparar_database([])

        self.usuario = {
            "role": "ar",
            "label_id": None,
        }

        respuesta = self.client.get(
            "/postulaciones/bandeja"
        )

        self.assertEqual(respuesta.status_code, 403)

        coleccion.find.assert_not_called()

    def test_bandeja_sin_resultados(self):
        coleccion, _ = self.preparar_database([])

        self.preparar_generos_disponibles()

        respuesta = self.client.get(
            "/postulaciones/bandeja"
        )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.json()

        self.assertEqual(datos["total"], 0)
        self.assertEqual(datos["postulaciones"], [])

        self.assertEqual(
            datos["generos_disponibles"],
            ["Metal", "Rock"],
        )

    def test_rechazar_genero_invalido(self):
        coleccion, _ = self.preparar_database([])

        normalizar = AsyncMock(
            side_effect=ValueError("Género inválido")
        )

        with patch.object(
            postulacion_route,
            "normalizar_generos_sello",
            new=normalizar,
        ):
            respuesta = self.client.get(
                "/postulaciones/bandeja",
                params={
                    "generos": "   ",
                },
            )

        self.assertEqual(respuesta.status_code, 422)

        coleccion.find.assert_not_called()


if __name__ == "__main__":
    unittest.main()
