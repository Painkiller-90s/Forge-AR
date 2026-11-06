
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.routes import spotify_route


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"
SPOTIFY_ID = "1234567890123456789012"
FECHA = "2026-11-05T20:00:00+00:00"

POSTULACION = {
    "_id": ObjectId(POSTULACION_ID),
    "sello_id": "sello_01",
    "press_kit": {
        "spotify_url": f"https://open.spotify.com/artist/{SPOTIFY_ID}"
    },
}

PERFIL = {
    "spotify_id": SPOTIFY_ID,
    "nombre": "Artista de prueba",
    "seguidores": 1500,
    "popularidad": 35,
    "fecha_obtencion": FECHA,
    "fuente": "Spotify Web API",
}

CATALOGO = {
    "spotify_id": SPOTIFY_ID,
    "total_lanzamientos": 5,
    "lanzamientos": [],
    "fecha_obtencion": FECHA,
    "fuente": "Spotify Web API",
}


class TestHU007SpotifyRoute(unittest.IsolatedAsyncioTestCase):

    async def test_consulta_guarda_metricas(self):
        base_simulada = SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(return_value=POSTULACION)
            )
        )

        with (
            patch.object(spotify_route, "database", base_simulada),
            patch.object(
                spotify_route,
                "consultar_artista_spotify",
                new=AsyncMock(return_value=dict(PERFIL)),
            ),
            patch.object(
                spotify_route,
                "consultar_catalogo_spotify",
                new=AsyncMock(return_value=dict(CATALOGO)),
            ),
            patch.object(
                spotify_route,
                "guardar_metricas_validas",
                new_callable=AsyncMock,
            ) as guardar,
        ):
            respuesta = await spotify_route.consultar_spotify_postulacion(
                POSTULACION_ID,
                current_user={
                    "role": "ar",
                    "label_id": "sello_01",
                },
            )

            self.assertEqual(
                respuesta["postulacion_id"],
                POSTULACION_ID,
            )
            self.assertEqual(
                respuesta["spotify_id"],
                SPOTIFY_ID,
            )
            self.assertEqual(
                respuesta["perfil"]["seguidores"],
                1500,
            )

            guardar.assert_awaited_once_with(
                postulacion_id=POSTULACION_ID,
                sello_id="sello_01",
                plataforma="spotify",
                cuenta_id=SPOTIFY_ID,
                metricas={
                    "perfil": PERFIL,
                    "catalogo": CATALOGO,
                    "fuente": "Spotify Web API",
                    "fecha_obtencion": FECHA,
                    "estado_metricas": "actualizadas",
                },
            )

    async def test_error_al_guardar_metricas(self):
        base_simulada = SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(return_value=POSTULACION)
            )
        )

        with (
            patch.object(spotify_route, "database", base_simulada),
            patch.object(
                spotify_route,
                "consultar_artista_spotify",
                new=AsyncMock(return_value=dict(PERFIL)),
            ),
            patch.object(
                spotify_route,
                "consultar_catalogo_spotify",
                new=AsyncMock(return_value=dict(CATALOGO)),
            ),
            patch.object(
                spotify_route,
                "guardar_metricas_validas",
                new=AsyncMock(
                    side_effect=RuntimeError("Fallo simulado de MongoDB")
                ),
            ),
            patch.object(spotify_route.logger, "error") as registrar_error,
        ):
            with self.assertRaises(HTTPException) as contexto:
                await spotify_route.consultar_spotify_postulacion(
                    POSTULACION_ID,
                    current_user={
                        "role": "ar",
                        "label_id": "sello_01",
                    },
                )

            self.assertEqual(
                contexto.exception.status_code,
                500,
            )

            registrar_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
