
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services import generos_service


def crear_database_simulada(generos):
    return SimpleNamespace(
        postulaciones=SimpleNamespace(
            distinct=AsyncMock(return_value=generos)
        )
    )


class TestHU011GenerosService(unittest.IsolatedAsyncioTestCase):

    async def test_obtener_generos_sin_duplicados(self):
        database_simulada = crear_database_simulada([
            "Rock",
            "rock",
            " ROCK ",
            "Metal",
            "Post-metal",
            None,
            " ",
        ])

        with patch.object(
            generos_service,
            "database",
            database_simulada,
        ):
            resultado = await generos_service.obtener_generos_sello(
                "sello_01"
            )

        self.assertEqual(
            resultado,
            ["Metal", "Post-metal", "Rock"],
        )

    async def test_normalizar_reutiliza_etiquetas_existentes(self):
        database_simulada = crear_database_simulada([
            "Rock",
            "Metal",
        ])

        with patch.object(
            generos_service,
            "database",
            database_simulada,
        ):
            resultado = await generos_service.normalizar_generos_sello(
                [" rock ", "METAL", "Punk", "punk"],
                "sello_01",
            )

        self.assertEqual(
            resultado,
            ["Rock", "Metal", "Punk"],
        )

    async def test_normalizar_aplica_alias_definido(self):
        database_simulada = crear_database_simulada([])

        with (
            patch.object(
                generos_service,
                "database",
                database_simulada,
            ),
            patch.dict(
                generos_service.ALIAS_GENEROS,
                {"post metal": "Post-metal"},
                clear=True,
            ),
        ):
            resultado = await generos_service.normalizar_generos_sello(
                ["Post Metal", "post-metal"],
                "sello_01",
            )

        self.assertEqual(resultado, ["Post-metal"])

    async def test_rechazar_etiqueta_vacia(self):
        database_simulada = crear_database_simulada([])

        with patch.object(
            generos_service,
            "database",
            database_simulada,
        ):
            with self.assertRaises(ValueError):
                await generos_service.normalizar_generos_sello(
                    ["   "],
                    "sello_01",
                )


if __name__ == "__main__":
    unittest.main()
