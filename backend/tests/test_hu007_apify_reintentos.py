
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import apify_service


class TestHU007ApifyReintentos(unittest.IsolatedAsyncioTestCase):

    async def test_configuracion_maximo_tres_intentos(self):
        cliente_simulado = MagicMock()

        actor_simulado = MagicMock()
        actor_simulado.call = AsyncMock(
            return_value=SimpleNamespace(
                default_dataset_id="dataset-prueba"
            )
        )

        dataset_simulado = MagicMock()
        dataset_simulado.list_items = AsyncMock(
            return_value=SimpleNamespace(
                items=[{"username": "scarcity.noise"}]
            )
        )

        cliente_simulado.actor.return_value = actor_simulado
        cliente_simulado.dataset.return_value = dataset_simulado

        with (
            patch.dict(
                apify_service.os.environ,
                {"APIFY_API_TOKEN": "token-de-prueba"},
            ),
            patch.object(
                apify_service,
                "ApifyClientAsync",
                return_value=cliente_simulado,
            ) as crear_cliente,
        ):
            resultado = await apify_service.consultar_perfil_instagram(
                "scarcity.noise"
            )

        crear_cliente.assert_called_once_with(
            token="token-de-prueba",
            max_retries=2,
        )

        cliente_simulado.actor.assert_called_once_with(
            apify_service.ACTOR_ID
        )

        actor_simulado.call.assert_awaited_once_with(
            run_input={"usernames": ["scarcity.noise"]}
        )

        dataset_simulado.list_items.assert_awaited_once_with(
            limit=1
        )

        self.assertEqual(
            resultado["username"],
            "scarcity.noise",
        )


if __name__ == "__main__":
    unittest.main()
