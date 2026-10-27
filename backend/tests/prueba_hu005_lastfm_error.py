
import asyncio
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from app.routes.lastfm_route import consultar_lastfm_postulacion


async def probar_error_lastfm():
    with (
        patch(
            "app.routes.lastfm_route.consultar_artista_spotify",
            new_callable=AsyncMock,
        ) as spotify_mock,
        patch(
            "app.routes.lastfm_route.obtener_metricas_lastfm_cache",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.routes.lastfm_route.consultar_artista_lastfm",
            new_callable=AsyncMock,
        ) as lastfm_mock,
    ):
        spotify_mock.return_value = {
            "nombre": "Neurosis",
            "url": "https://open.spotify.com/artist/1KHydwFySZY3YcWyo2q2dF",
        }

        # Simular una falla del servicio de Last.fm.
        lastfm_mock.side_effect = RuntimeError(
            "Last.fm no disponible: prueba controlada"
        )

        try:
            await consultar_lastfm_postulacion(
                postulacion_id="6ad9176ebb20e72c8d38c558",
                current_user={
                    "role": "ar",
                    "label_id": "sello_01",
                },
            )

        except HTTPException as error:
            print("Código HTTP:", error.status_code)
            print("Mensaje:", error.detail)

        else:
            print("ERROR: La falla no fue controlada.")


asyncio.run(probar_error_lastfm())
