
import unittest

from app.services.viability_service import calcular_q_rrss


class TestCalcularQRRSS(unittest.TestCase):

    def crear_metricas(
        self,
        seguidores=2000,
        publicaciones=None,
        total=3,
    ):
        if publicaciones is None:
            publicaciones = [
                {"likes": 80, "comentarios": 20, "es_propia": True},
                {"likes": 100, "comentarios": 0, "es_propia": True},
                {"likes": 60, "comentarios": 20, "es_propia": True},
            ]

        return {
            "seguidores": seguidores,
            "publicaciones_totales": total,
            "publicaciones": publicaciones,
            "fuente": "Apify Instagram Profile Scraper",
            "estado_metricas": "actualizadas",
            "fecha_obtencion": "2026-11-12T12:00:00Z",
        }

    def test_ejemplo_aprobado(self):
        resultado = calcular_q_rrss(self.crear_metricas())

        self.assertEqual(resultado["q_rrss"], 80)
        self.assertEqual(resultado["puntaje_likes"], 40)
        self.assertEqual(resultado["puntaje_comentarios"], 40)
        self.assertEqual(resultado["likes_promedio"], 80)
        self.assertEqual(resultado["comentarios_promedio"], 13.33)
        self.assertEqual(resultado["publicaciones_evaluadas"], 3)

    def test_puntaje_maximo(self):
        metricas = self.crear_metricas(
            seguidores=100,
            publicaciones=[
                {"likes": 10, "comentarios": 2, "es_propia": True}
            ],
            total=1,
        )

        self.assertEqual(calcular_q_rrss(metricas)["q_rrss"], 100)

    def test_ignorar_publicaciones_ajenas(self):
        metricas = self.crear_metricas(
            publicaciones=[
                {"likes": 80, "comentarios": 20, "es_propia": True},
                {"likes": 5000, "comentarios": 500, "es_propia": False},
            ],
        )

        resultado = calcular_q_rrss(metricas)

        self.assertEqual(resultado["publicaciones_evaluadas"], 1)
        self.assertEqual(resultado["likes_promedio"], 80)

    def test_sin_propietario_confirmado(self):
        metricas = self.crear_metricas(
            publicaciones=[
                {"likes": 100, "comentarios": 10, "es_propia": None}
            ],
        )

        self.assertIsNone(calcular_q_rrss(metricas))

    def test_perfil_sin_publicaciones(self):
        metricas = self.crear_metricas(
            publicaciones=[],
            total=0,
        )

        self.assertEqual(calcular_q_rrss(metricas)["q_rrss"], 0)

    def test_sin_publicaciones_recuperadas(self):
        metricas = self.crear_metricas(
            publicaciones=[],
            total=10,
        )

        self.assertIsNone(calcular_q_rrss(metricas))

    def test_sin_seguidores(self):
        metricas = self.crear_metricas(seguidores=0)

        self.assertIsNone(calcular_q_rrss(metricas))

    def test_rechazar_seguidores_negativos(self):
        metricas = self.crear_metricas(seguidores=-100)

        with self.assertRaises(ValueError):
            calcular_q_rrss(metricas)

    def test_ignorar_publicacion_con_metricas_invalidas(self):
        metricas = self.crear_metricas(
            publicaciones=[
                {"likes": -50, "comentarios": 10, "es_propia": True},
                {"likes": 80, "comentarios": 20, "es_propia": True},
            ],
        )

        resultado = calcular_q_rrss(metricas)

        self.assertEqual(resultado["publicaciones_evaluadas"], 1)
        self.assertEqual(resultado["likes_promedio"], 80)

    def test_conservar_trazabilidad(self):
        resultado = calcular_q_rrss(self.crear_metricas())

        self.assertEqual(
            resultado["fuente"],
            "Apify Instagram Profile Scraper",
        )
        self.assertEqual(
            resultado["estado_metricas"],
            "actualizadas",
        )


if __name__ == "__main__":
    unittest.main()