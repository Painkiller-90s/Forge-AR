
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId

from app.services import evaluacion_service as service


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"
SPOTIFY_ID = "1234567890123456789012"
FECHA = "2026-11-14T12:00:00+00:00"


POSTULACION = {
    "_id": ObjectId(POSTULACION_ID),
    "sello_id": "sello_01",
    "press_kit": {
        "nombre_artistico": "Mi Banda",
        "spotify_url": (
            f"https://open.spotify.com/artist/{SPOTIFY_ID}"
        ),
        "instagram_url": (
            "https://www.instagram.com/mi.banda/"
        ),
    },
    "demos": [
        {
            "nombre": "Demo 1",
            "archivo_id": "archivo_001",
        }
    ],
}


SPOTIFY = {
    "perfil": {
        "spotify_id": SPOTIFY_ID,
        "nombre": "Mi Banda",
        "fecha_obtencion": FECHA,
    },
    "catalogo": {
        "albumes": [],
        "canciones": [],
    },
    "fuente": "Spotify Web API",
    "fecha_obtencion": FECHA,
    "estado_metricas": "actualizadas",
}


INSTAGRAM = {
    "username": "mi.banda",
    "seguidores": 2000,
    "publicaciones": [],
    "fuente": "Apify Instagram Profile Scraper",
    "fecha_obtencion": FECHA,
    "estado_metricas": "actualizadas",
}


LASTFM = {
    "nombre": "Mi Banda",
    "mbid": "mbid-ejemplo",
    "url": "https://www.last.fm/music/Mi+Banda",
    "oyentes_acumulados": 800,
    "reproducciones_acumuladas": 16000,
    "fuente": "Last.fm API",
    "fecha_obtencion": FECHA,
    "estado_metricas": "actualizadas",
}


RECOPILACION_COMPLETA = {
    "spotify": SPOTIFY,
    "instagram": INSTAGRAM,
    "lastfm": LASTFM,
    "perfil_lastfm_encontrado": True,
    "identidad_confirmada": True,
}


VIABILIDAD_EVALUABLE = {
    "estado": "evaluable",
    "score": 85.5,
    "nivel_riesgo": "bajo",
    "dimensiones": {},
    "aportes": {},
    "dimensiones_faltantes": [],
    "motivos_no_evaluable": [],
}


VIABILIDAD_NO_EVALUABLE = {
    "estado": "no_evaluable",
    "score": None,
    "nivel_riesgo": None,
    "dimensiones": {},
    "aportes": None,
    "dimensiones_faltantes": [
        "q_streaming",
        "q_rrss",
        "q_consistencia",
    ],
    "motivos_no_evaluable": [
        "Faltan métricas externas.",
    ],
}


class TestHU009EvaluacionService(
    unittest.IsolatedAsyncioTestCase
):

    def crear_database(self, postulacion=POSTULACION):

        return SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(
                    return_value=postulacion
                )
            )
        )

    async def test_generar_evaluacion_completa(self):

        base = self.crear_database()

        with (
            patch.object(
                service,
                "database",
                base,
            ),
            patch.object(
                service,
                "recopilar_metricas_evaluacion",
                new_callable=AsyncMock,
                return_value=RECOPILACION_COMPLETA,
            ) as recopilar,
            patch.object(
                service,
                "calcular_q_audio_postulacion",
                return_value=90,
            ) as q_audio,
            patch.object(
                service,
                "calcular_q_streaming",
                return_value={
                    "q_streaming": 85,
                },
            ) as q_streaming,
            patch.object(
                service,
                "calcular_q_rrss",
                return_value={
                    "q_rrss": 75,
                },
            ) as q_rrss,
            patch.object(
                service,
                "calcular_q_presskit",
                return_value={
                    "estado": "evaluable",
                    "q_presskit": 80,
                },
            ) as q_presskit,
            patch.object(
                service,
                "calcular_q_consistencia",
                return_value={
                    "estado": "evaluable",
                    "q_consistencia": 100,
                },
            ) as q_consistencia,
            patch.object(
                service,
                "calcular_score_viabilidad",
                return_value=VIABILIDAD_EVALUABLE,
            ) as calcular_score,
        ):

            resultado = await service.generar_evaluacion_actual(
                POSTULACION_ID,
                "sello_01",
            )

            # Comprobar que existe una evaluación.
            self.assertIsNotNone(resultado)

            # Comprobar la recopilación automática.
            recopilar.assert_awaited_once_with(
                postulacion_id=POSTULACION_ID,
                sello_id="sello_01",
            )

            # Comprobar las cinco dimensiones.
            q_audio.assert_called_once_with(
                POSTULACION["demos"]
            )

            q_streaming.assert_called_once_with(
                metricas=LASTFM,
                identidad_confirmada=True,
                perfil_encontrado=True,
            )

            q_rrss.assert_called_once_with(
                INSTAGRAM
            )

            q_presskit.assert_called_once_with(
                POSTULACION["press_kit"]
            )

            # Comprobar la preparación de Q_consistencia.
            argumentos = q_consistencia.call_args.args

            self.assertEqual(
                argumentos[0],
                POSTULACION,
            )

            self.assertEqual(
                argumentos[1],
                SPOTIFY,
            )

            self.assertEqual(
                argumentos[2]["lastfm"],
                LASTFM,
            )

            self.assertTrue(
                argumentos[2]["identidad_confirmada"]
            )

            self.assertEqual(
                argumentos[3],
                {"instagram": INSTAGRAM},
            )

            # Comprobar el Score general.
            calcular_score.assert_called_once_with(
                q_audio=90,
                q_streaming={"q_streaming": 85},
                q_rrss={"q_rrss": 75},
                q_presskit={
                    "estado": "evaluable",
                    "q_presskit": 80,
                },
                q_consistencia={
                    "estado": "evaluable",
                    "q_consistencia": 100,
                },
            )

            self.assertEqual(
                resultado["viabilidad"]["estado"],
                "evaluable",
            )

            self.assertEqual(
                resultado["viabilidad"]["score"],
                85.5,
            )

            self.assertEqual(
                resultado["viabilidad"]["nivel_riesgo"],
                "bajo",
            )

            # Comprobar las fuentes.
            self.assertTrue(
                resultado["fuentes"]["spotify"]["disponible"]
            )

            self.assertTrue(
                resultado["fuentes"]["instagram"]["disponible"]
            )

            self.assertTrue(
                resultado["fuentes"]["lastfm"]["disponible"]
            )

            self.assertTrue(
                resultado["fuentes"]["lastfm"][
                    "identidad_confirmada"
                ]
            )

            # Comprobar la trazabilidad.
            self.assertEqual(
                resultado["datos_utilizados"]["spotify"],
                SPOTIFY,
            )

            self.assertEqual(
                resultado["datos_utilizados"]["instagram"],
                INSTAGRAM,
            )

            self.assertEqual(
                resultado["datos_utilizados"]["lastfm"],
                LASTFM,
            )

    async def test_evaluacion_no_evaluable(self):

        base = self.crear_database()

        recopilacion = {
            "spotify": None,
            "instagram": None,
            "lastfm": None,
            "perfil_lastfm_encontrado": None,
            "identidad_confirmada": False,
        }

        with (
            patch.object(
                service,
                "database",
                base,
            ),
            patch.object(
                service,
                "recopilar_metricas_evaluacion",
                new_callable=AsyncMock,
                return_value=recopilacion,
            ),
            patch.object(
                service,
                "calcular_q_audio_postulacion",
                return_value=93,
            ),
            patch.object(
                service,
                "calcular_q_streaming",
            ) as q_streaming,
            patch.object(
                service,
                "calcular_q_rrss",
            ) as q_rrss,
            patch.object(
                service,
                "calcular_q_presskit",
                return_value={
                    "estado": "evaluable",
                    "q_presskit": 70,
                },
            ),
            patch.object(
                service,
                "calcular_q_consistencia",
                return_value={
                    "estado": "no_evaluable",
                    "q_consistencia": None,
                },
            ),
            patch.object(
                service,
                "calcular_score_viabilidad",
                return_value=VIABILIDAD_NO_EVALUABLE,
            ) as calcular_score,
        ):

            resultado = await service.generar_evaluacion_actual(
                POSTULACION_ID,
                "sello_01",
            )

            self.assertEqual(
                resultado["viabilidad"]["estado"],
                "no_evaluable",
            )

            self.assertIsNone(
                resultado["viabilidad"]["score"]
            )

            self.assertIsNone(
                resultado["viabilidad"]["nivel_riesgo"]
            )

            # Sin Last.fm ni perfil confirmado,
            # Q_streaming queda sin evaluación.
            q_streaming.assert_not_called()

            # Sin Instagram, Q_rrss queda sin evaluación.
            q_rrss.assert_not_called()

            # Comprobar que el Score recibe las dimensiones faltantes.
            argumentos = calcular_score.call_args.kwargs

            self.assertEqual(
                argumentos["q_audio"],
                93,
            )

            self.assertIsNone(
                argumentos["q_streaming"]
            )

            self.assertIsNone(
                argumentos["q_rrss"]
            )

            self.assertIsNone(
                resultado["datos_utilizados"]["lastfm"]
            )

            self.assertFalse(
                resultado["fuentes"]["lastfm"]["disponible"]
            )

    async def test_artista_no_encontrado_en_lastfm(self):

        base = self.crear_database()

        recopilacion = {
            "spotify": SPOTIFY,
            "instagram": INSTAGRAM,
            "lastfm": None,
            "perfil_lastfm_encontrado": False,
            "identidad_confirmada": False,
        }

        with (
            patch.object(
                service,
                "database",
                base,
            ),
            patch.object(
                service,
                "recopilar_metricas_evaluacion",
                new_callable=AsyncMock,
                return_value=recopilacion,
            ),
            patch.object(
                service,
                "calcular_q_audio_postulacion",
                return_value=90,
            ),
            patch.object(
                service,
                "calcular_q_streaming",
                return_value={
                    "q_streaming": 0,
                    "puntaje_audiencia": 0,
                    "puntaje_fidelidad": 0,
                    "ratio_reproducciones_oyente": 0.0,
                },
            ) as q_streaming,
            patch.object(
                service,
                "calcular_q_rrss",
                return_value={"q_rrss": 70},
            ),
            patch.object(
                service,
                "calcular_q_presskit",
                return_value={"q_presskit": 80},
            ),
            patch.object(
                service,
                "calcular_q_consistencia",
                return_value={
                    "estado": "no_evaluable",
                    "q_consistencia": None,
                },
            ),
            patch.object(
                service,
                "calcular_score_viabilidad",
                return_value=VIABILIDAD_NO_EVALUABLE,
            ),
        ):

            resultado = await service.generar_evaluacion_actual(
                POSTULACION_ID,
                "sello_01",
            )

            # Un artista inexistente recibe cero puntos
            # en Q_streaming, no None.
            q_streaming.assert_called_once_with(
                metricas=None,
                identidad_confirmada=False,
                perfil_encontrado=False,
            )

            self.assertEqual(
                resultado["fuentes"]["lastfm"][
                    "perfil_encontrado"
                ],
                False,
            )

            self.assertFalse(
                resultado["fuentes"]["lastfm"][
                    "identidad_confirmada"
                ]
            )

    async def test_preservar_metricas_desactualizadas(self):

        base = self.crear_database()

        spotify_historico = {
            **SPOTIFY,
            "estado_metricas": "desactualizadas",
        }

        instagram_historico = {
            **INSTAGRAM,
            "estado_metricas": "desactualizadas",
        }

        lastfm_historico = {
            **LASTFM,
            "estado_metricas": "desactualizadas",
        }

        recopilacion = {
            "spotify": spotify_historico,
            "instagram": instagram_historico,
            "lastfm": lastfm_historico,
            "perfil_lastfm_encontrado": True,
            "identidad_confirmada": True,
        }

        with (
            patch.object(
                service,
                "database",
                base,
            ),
            patch.object(
                service,
                "recopilar_metricas_evaluacion",
                new_callable=AsyncMock,
                return_value=recopilacion,
            ),
            patch.object(
                service,
                "calcular_q_audio_postulacion",
                return_value=90,
            ),
            patch.object(
                service,
                "calcular_q_streaming",
                return_value={"q_streaming": 80},
            ) as q_streaming,
            patch.object(
                service,
                "calcular_q_rrss",
                return_value={"q_rrss": 70},
            ) as q_rrss,
            patch.object(
                service,
                "calcular_q_presskit",
                return_value={"q_presskit": 80},
            ),
            patch.object(
                service,
                "calcular_q_consistencia",
                return_value={
                    "estado": "evaluable",
                    "q_consistencia": 100,
                    "fuentes_desactualizadas": [
                        "spotify",
                        "instagram",
                        "lastfm",
                    ],
                },
            ) as q_consistencia,
            patch.object(
                service,
                "calcular_score_viabilidad",
                return_value=VIABILIDAD_EVALUABLE,
            ),
        ):

            resultado = await service.generar_evaluacion_actual(
                POSTULACION_ID,
                "sello_01",
            )

            # Las métricas históricas siguen siendo utilizables
            # si Last.fm confirmó la identidad.
            q_streaming.assert_called_once_with(
                metricas=lastfm_historico,
                identidad_confirmada=True,
                perfil_encontrado=True,
            )

            q_rrss.assert_called_once_with(
                instagram_historico
            )

            # Comprobar que las tres fuentes llegan
            # completas a Q_consistencia.
            argumentos = q_consistencia.call_args.args

            self.assertEqual(
                argumentos[1],
                spotify_historico,
            )

            self.assertEqual(
                argumentos[2]["lastfm"],
                lastfm_historico,
            )

            self.assertEqual(
                argumentos[3],
                {"instagram": instagram_historico},
            )

            # Comprobar que se conserva el estado histórico.
            datos = resultado["datos_utilizados"]

            self.assertEqual(
                datos["spotify"]["estado_metricas"],
                "desactualizadas",
            )

            self.assertEqual(
                datos["instagram"]["estado_metricas"],
                "desactualizadas",
            )

            self.assertEqual(
                datos["lastfm"]["estado_metricas"],
                "desactualizadas",
            )

    async def test_postulacion_no_encontrada(self):

        base = self.crear_database(postulacion=None)

        with (
            patch.object(
                service,
                "database",
                base,
            ),
            patch.object(
                service,
                "recopilar_metricas_evaluacion",
                new_callable=AsyncMock,
            ) as recopilar,
        ):

            resultado = await service.generar_evaluacion_actual(
                POSTULACION_ID,
                "sello_01",
            )

            self.assertIsNone(resultado)

            recopilar.assert_not_awaited()

    async def test_recopilacion_no_disponible(self):

        base = self.crear_database()

        with (
            patch.object(
                service,
                "database",
                base,
            ),
            patch.object(
                service,
                "recopilar_metricas_evaluacion",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch.object(
                service,
                "calcular_q_audio_postulacion",
            ) as q_audio,
            patch.object(
                service,
                "calcular_score_viabilidad",
            ) as calcular_score,
        ):

            resultado = await service.generar_evaluacion_actual(
                POSTULACION_ID,
                "sello_01",
            )

            self.assertIsNone(resultado)

            q_audio.assert_not_called()
            calcular_score.assert_not_called()


if __name__ == "__main__":
    unittest.main()
