
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.routes import viabilidad_route
from tests.test_hu008_integracion_datos import (
    crear_datos,
    SPOTIFY_ID,
)


POSTULACION_ID = "6ad9176ebb20e72c8d38c558"

USUARIO_AR = {
    "role": "ar",
    "label_id": "sello_01",
}


class TestHU008ViabilidadRoute(
    unittest.IsolatedAsyncioTestCase
):

    def crear_database(
        self,
        con_metricas=True,
        con_identidad=True,
        postulacion_existe=True,
    ):
        postulacion, spotify, lastfm, instagram = crear_datos()

        postulacion["_id"] = ObjectId(POSTULACION_ID)
        postulacion["sello_id"] = "sello_01"

        async def obtener_metricas(filtro):
            if not con_metricas:
                return None

            if filtro["plataforma"] == "spotify":
                return {"metricas": spotify}

            if filtro["plataforma"] == "instagram":
                return {"metricas": instagram["instagram"]}

            return None

        return SimpleNamespace(
            postulaciones=SimpleNamespace(
                find_one=AsyncMock(
                    return_value=(
                        postulacion
                        if postulacion_existe
                        else None
                    )
                ),
            ),
            metricas_externas=SimpleNamespace(
                find_one=AsyncMock(
                    side_effect=obtener_metricas
                ),
            ),
            lastfm_cache=SimpleNamespace(
                find_one=AsyncMock(
                    return_value={
                        "_id": SPOTIFY_ID,
                        **lastfm["lastfm"],
                    },
                ),
            ),
            identidades_artistas=SimpleNamespace(
                find_one=AsyncMock(
                    return_value=(
                        {"identidad_confirmada": True}
                        if con_identidad
                        else None
                    ),
                ),
            ),
        )

    async def test_calcular_score_desde_mongodb(self):
        base = self.crear_database()

        with patch.object(viabilidad_route, "database", base):
            resultado = await (
                viabilidad_route.consultar_viabilidad_postulacion(
                    POSTULACION_ID,
                    current_user=USUARIO_AR,
                )
            )

        self.assertEqual(
            resultado["viabilidad"]["score"],
            81,
        )
        self.assertEqual(
            resultado["viabilidad"]["nivel_riesgo"],
            "bajo",
        )
        self.assertTrue(
            resultado["fuentes"]["lastfm"][
                "identidad_confirmada"
            ]
        )

        base.identidades_artistas.find_one.assert_awaited_once_with({
            "_id": SPOTIFY_ID,
            "musicbrainz_mbid": "mbid-ejemplo",
            "identidad_confirmada": True,
        })

    async def test_sin_metricas_no_evaluable(self):
        base = self.crear_database(con_metricas=False)

        with patch.object(viabilidad_route, "database", base):
            resultado = await (
                viabilidad_route.consultar_viabilidad_postulacion(
                    POSTULACION_ID,
                    current_user=USUARIO_AR,
                )
            )

        self.assertIsNone(
            resultado["viabilidad"]["score"]
        )
        self.assertEqual(
            resultado["viabilidad"]["estado"],
            "no_evaluable",
        )

    async def test_identidad_pendiente(self):
        base = self.crear_database(con_identidad=False)

        with patch.object(viabilidad_route, "database", base):
            resultado = await (
                viabilidad_route.consultar_viabilidad_postulacion(
                    POSTULACION_ID,
                    current_user=USUARIO_AR,
                )
            )

        self.assertIsNone(
            resultado["viabilidad"]["score"]
        )
        self.assertFalse(
            resultado["fuentes"]["lastfm"][
                "identidad_confirmada"
            ]
        )

    async def test_rechazar_usuario_sin_rol_ar(self):
        base = self.crear_database()

        with patch.object(viabilidad_route, "database", base):
            with self.assertRaises(HTTPException) as contexto:
                await (
                    viabilidad_route.consultar_viabilidad_postulacion(
                        POSTULACION_ID,
                        current_user={
                            "role": "admin",
                            "label_id": "sello_01",
                        },
                    )
                )

        self.assertEqual(contexto.exception.status_code, 403)
        base.postulaciones.find_one.assert_not_awaited()

    async def test_aislamiento_por_sello(self):
        base = self.crear_database(postulacion_existe=False)

        with patch.object(viabilidad_route, "database", base):
            with self.assertRaises(HTTPException) as contexto:
                await (
                    viabilidad_route.consultar_viabilidad_postulacion(
                        POSTULACION_ID,
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(contexto.exception.status_code, 404)

        filtro = base.postulaciones.find_one.call_args.args[0]
        self.assertEqual(filtro["sello_id"], "sello_01")

    async def test_rechazar_id_invalido(self):
        base = self.crear_database()

        with patch.object(viabilidad_route, "database", base):
            with self.assertRaises(HTTPException) as contexto:
                await (
                    viabilidad_route.consultar_viabilidad_postulacion(
                        "id-invalido",
                        current_user=USUARIO_AR,
                    )
                )

        self.assertEqual(contexto.exception.status_code, 400)

    async def test_metricas_filtradas_por_cuenta(self):
        base = self.crear_database()

        with patch.object(viabilidad_route, "database", base):
            await viabilidad_route.consultar_viabilidad_postulacion(
                POSTULACION_ID,
                current_user=USUARIO_AR,
            )

        consultas = [
            llamada.args[0]
            for llamada in base.metricas_externas.find_one.call_args_list
        ]

        self.assertEqual(len(consultas), 2)

        self.assertTrue(
            all(
                consulta["postulacion_id"] == POSTULACION_ID
                and consulta["sello_id"] == "sello_01"
                for consulta in consultas
            )
        )

        self.assertTrue(
            any(
                consulta["plataforma"] == "spotify"
                and consulta["cuenta_id"] == SPOTIFY_ID
                for consulta in consultas
            )
        )


if __name__ == "__main__":
    unittest.main()
