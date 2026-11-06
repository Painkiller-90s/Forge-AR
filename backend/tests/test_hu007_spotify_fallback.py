
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.routes import spotify_route


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"
SPOTIFY_ID = "1234567890123456789012"

POSTULACION = {
    "_id": ObjectId(POSTULACION_ID),
    "sello_id": "sello_01",
    "press_kit": {
        "spotify_url": f"https://open.spotify.com/artist/{SPOTIFY_ID}"
    },
}

RESPALDO = {
    "perfil": {
        "nombre": "Artista de prueba",
        "seguidores": 1500,
        "popularidad": 35,
    },
    "catalogo": {
        "total_lanzamientos": 5,
        "lanzamientos": [],
    },
    "fuente": "Spotify Web API",
    "fecha_obtencion": "2026-11-05T20:00:00+00:00",
    "estado_metricas": "desactualizadas",
}


class TestHU007SpotifyFallback(unittest.IsolatedAsyncioTestCase):

    async def test_fallo_spotify_con_respaldo(self):
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
                new=AsyncMock(
                    side_effect=RuntimeError("Spotify no disponible")
                ),
            ),
            patch.object(
                spotify_route,
                "recuperar_ultimas_metricas",
                new_callable=AsyncMock,
            ) as recuperar,
            patch.object(
                spotify_route,
                "guardar_metricas_validas",
                new_callable=AsyncMock,
            ) as guardar,
            patch.object(
                spotify_route.logger,
                "error",
            ) as registrar_error,
        ):
            recuperar.return_value = dict(RESPALDO)

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
                respuesta["perfil"]["seguidores"],
                1500,
            )
            self.assertEqual(
                respuesta["estado_metricas"],
                "desactualizadas",
            )
            self.assertEqual(
                respuesta["fecha_obtencion"],
                RESPALDO["fecha_obtencion"],
            )

            recuperar.assert_awaited_once_with(
                postulacion_id=POSTULACION_ID,
                sello_id="sello_01",
                plataforma="spotify",
                cuenta_id=SPOTIFY_ID,
            )

            guardar.assert_not_awaited()
            # CA07: comprobar el registro del error de Spotify.
            registrar_error.assert_called_once()

            argumentos = registrar_error.call_args.args

            self.assertIn("HU007", argumentos[0])
            self.assertEqual(argumentos[1], POSTULACION_ID)
            self.assertEqual(argumentos[2], "RuntimeError")

    async def test_fallo_spotify_sin_respaldo(self):
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
                new=AsyncMock(
                    side_effect=RuntimeError("Spotify no disponible")
                ),
            ),
            patch.object(
                spotify_route,
                "recuperar_ultimas_metricas",
                new=AsyncMock(return_value=None),
            ),
            patch.object(spotify_route.logger, "error"),
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
                502,
            )

    async def test_actualizar_no_sobrescribe_respaldo(self):
        cache_simulada = SimpleNamespace(
            create_index=AsyncMock(),
            update_one=AsyncMock(),
        )

        base_simulada = SimpleNamespace(
            spotify_cache=cache_simulada
        )

        respuesta_respaldo = {
            "postulacion_id": POSTULACION_ID,
            "spotify_id": SPOTIFY_ID,
            **RESPALDO,
        }

        with (
            patch.object(spotify_route, "database", base_simulada),
            patch.object(
                spotify_route,
                "consultar_spotify_postulacion",
                new=AsyncMock(return_value=respuesta_respaldo),
            ),
        ):
            respuesta = await spotify_route.actualizar_spotify_postulacion(
                POSTULACION_ID,
                current_user={
                    "role": "ar",
                    "label_id": "sello_01",
                },
            )

            self.assertEqual(
                respuesta["estado_metricas"],
                "desactualizadas",
            )

            cache_simulada.create_index.assert_not_awaited()
            cache_simulada.update_one.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
