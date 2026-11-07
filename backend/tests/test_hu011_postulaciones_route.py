
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.routes import postulacion_route


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"

FECHA = datetime(2026, 11, 7, tzinfo=timezone.utc)


def crear_postulacion(nombre, generos):
    return {
        "_id": ObjectId(POSTULACION_ID),
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


def crear_database_simulada(postulaciones):
    cursor = Mock()
    cursor.sort.return_value = cursor
    cursor.to_list = AsyncMock(return_value=postulaciones)

    coleccion = SimpleNamespace(
        find=Mock(return_value=cursor)
    )

    return (
        SimpleNamespace(postulaciones=coleccion),
        coleccion,
        cursor,
    )


class TestHU011PostulacionesRoute(unittest.IsolatedAsyncioTestCase):

    async def test_listar_postulaciones_del_sello(self):
        documentos = [
            crear_postulacion("Artista A", ["Rock"]),
            crear_postulacion("Artista B", ["Metal"]),
        ]

        base, coleccion, cursor = crear_database_simulada(documentos)

        with (
            patch.object(postulacion_route, "database", base),
            patch.object(
                postulacion_route,
                "obtener_generos_sello",
                new=AsyncMock(return_value=["Metal", "Rock"]),
            ),
        ):
            respuesta = await postulacion_route.listar_bandeja_postulaciones(
                generos=None,
                current_user={
                    "role": "ar",
                    "label_id": "sello_01",
                },
            )

        coleccion.find.assert_called_once_with({
            "sello_id": "sello_01",
        })

        cursor.sort.assert_called_once_with("created_at", -1)
        cursor.to_list.assert_awaited_once_with(length=None)

        self.assertEqual(respuesta["total"], 2)
        self.assertEqual(
            respuesta["generos_disponibles"],
            ["Metal", "Rock"],
        )
        self.assertEqual(
            respuesta["postulaciones"][0]["nombre_artistico"],
            "Artista A",
        )

    async def test_filtro_generos_utiliza_or(self):
        documentos = [
            crear_postulacion("Artista A", ["Rock"]),
            crear_postulacion("Artista B", ["Metal"]),
        ]

        base, coleccion, _ = crear_database_simulada(documentos)

        with (
            patch.object(postulacion_route, "database", base),
            patch.object(
                postulacion_route,
                "normalizar_generos_sello",
                new=AsyncMock(return_value=["Rock", "Metal"]),
            ) as normalizar,
            patch.object(
                postulacion_route,
                "obtener_generos_sello",
                new=AsyncMock(return_value=["Metal", "Rock"]),
            ),
        ):
            respuesta = await postulacion_route.listar_bandeja_postulaciones(
                generos=["rock", "METAL"],
                current_user={
                    "role": "ar",
                    "label_id": "sello_01",
                },
            )

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

        self.assertEqual(respuesta["total"], 2)

    async def test_rechazar_usuario_sin_rol_ar(self):
        base, coleccion, _ = crear_database_simulada([])

        with patch.object(postulacion_route, "database", base):
            with self.assertRaises(HTTPException) as contexto:
                await postulacion_route.listar_bandeja_postulaciones(
                    generos=None,
                    current_user={
                        "role": "artista",
                        "label_id": "sello_01",
                    },
                )

        self.assertEqual(contexto.exception.status_code, 403)
        coleccion.find.assert_not_called()

    async def test_rechazar_usuario_sin_sello(self):
        base, coleccion, _ = crear_database_simulada([])

        with patch.object(postulacion_route, "database", base):
            with self.assertRaises(HTTPException) as contexto:
                await postulacion_route.listar_bandeja_postulaciones(
                    generos=None,
                    current_user={
                        "role": "ar",
                        "label_id": None,
                    },
                )

        self.assertEqual(contexto.exception.status_code, 403)
        coleccion.find.assert_not_called()

    async def test_bandeja_sin_resultados(self):
        base, _, _ = crear_database_simulada([])

        with (
            patch.object(postulacion_route, "database", base),
            patch.object(
                postulacion_route,
                "obtener_generos_sello",
                new=AsyncMock(return_value=["Rock", "Metal"]),
            ),
        ):
            respuesta = await postulacion_route.listar_bandeja_postulaciones(
                generos=None,
                current_user={
                    "role": "ar",
                    "label_id": "sello_01",
                },
            )

        self.assertEqual(respuesta["total"], 0)
        self.assertEqual(respuesta["postulaciones"], [])
        self.assertEqual(
            respuesta["generos_disponibles"],
            ["Rock", "Metal"],
        )

    async def test_rechazar_genero_invalido(self):
        base, coleccion, _ = crear_database_simulada([])

        with (
            patch.object(postulacion_route, "database", base),
            patch.object(
                postulacion_route,
                "normalizar_generos_sello",
                new=AsyncMock(
                    side_effect=ValueError("Género inválido")
                ),
            ),
        ):
            with self.assertRaises(HTTPException) as contexto:
                await postulacion_route.listar_bandeja_postulaciones(
                    generos=["   "],
                    current_user={
                        "role": "ar",
                        "label_id": "sello_01",
                    },
                )

        self.assertEqual(contexto.exception.status_code, 422)
        coleccion.find.assert_not_called()


if __name__ == "__main__":
    unittest.main()
