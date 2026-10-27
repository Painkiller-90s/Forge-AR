
import asyncio
from unittest.mock import AsyncMock, patch

from app.routes.lastfm_route import consultar_lastfm_postulacion


async def probar_actualizacion_cache():
    with (
        patch(
            "app.routes.lastfm_route.consultar_artista_spotify",
            new_callable=AsyncMock,
        ) as spotify_mock,
        patch(
            "app.routes.lastfm_route.obtener_metricas_lastfm_cache",
            new_callable=AsyncMock,
        ) as cache_mock,
        patch(
            "app.routes.lastfm_route.consultar_artista_lastfm",
            new_callable=AsyncMock,
        ) as lastfm_mock,
        patch(
            "app.routes.lastfm_route.verificar_identidad_con_cache",
            new_callable=AsyncMock,
        ) as identidad_mock,
        patch(
            "app.routes.lastfm_route.guardar_metricas_lastfm_cache",
            new_callable=AsyncMock,
        ) as guardar_mock,
    ):
        spotify_mock.return_value = {
            "nombre": "Neurosis",
            "url": "https://open.spotify.com/artist/1KHydwFySZY3YcWyo2q2dF",
        }

        # Simular caché expirada.
        cache_mock.return_value = None

        # Simular estadísticas actualizadas.
        lastfm_mock.return_value = {
            "nombre": "Neurosis",
            "mbid": "a9416fb3-4d28-4575-abae-f0d160be83ed",
            "url": "https://www.last.fm/music/Neurosis",
            "oyentes_acumulados": 360000,
            "reproducciones_acumuladas": 18600000,
            "fuente": "Last.fm API",
            "fecha_obtencion": "2026-10-27T22:00:00+00:00",
        }

        identidad_mock.return_value = False

        resultado = await consultar_lastfm_postulacion(
            "6ad9176ebb20e72c8d38c558",
            {"role": "ar", "label_id": "sello_01"},
        )

        print("Consultas a Last.fm:", lastfm_mock.await_count)
        print("Guardados en caché:", guardar_mock.await_count)
        print("Estado:", resultado["estado"])
        print("Oyentes:", resultado["lastfm"]["oyentes_acumulados"])


asyncio.run(probar_actualizacion_cache())
