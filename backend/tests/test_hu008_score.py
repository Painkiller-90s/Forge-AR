
import unittest

from app.services.viability_service import (
    calcular_score_viabilidad,
)


class TestScoreViabilidad(unittest.TestCase):

    def calcular(
        self,
        audio=80,
        streaming=60,
        rrss=70,
        presskit=90,
        consistencia=100,
    ):
        return calcular_score_viabilidad(
            q_audio=audio,
            q_streaming=(
                {"q_streaming": streaming}
                if streaming is not None
                else None
            ),
            q_rrss={"q_rrss": rrss},
            q_presskit={"q_presskit": presskit},
            q_consistencia={
                "q_consistencia": consistencia
            },
        )

    def test_score_ponderado(self):
        resultado = self.calcular()

        self.assertEqual(resultado["score"], 75)
        self.assertEqual(resultado["nivel_riesgo"], "bajo")
        self.assertEqual(resultado["aportes"]["q_audio"], 24)
        self.assertEqual(
            resultado["aportes"]["q_streaming"], 18
        )

    def test_puntaje_maximo(self):
        resultado = self.calcular(
            100, 100, 100, 100, 100
        )

        self.assertEqual(resultado["score"], 100)

    def test_puntaje_minimo(self):
        resultado = self.calcular(0, 0, 0, 0, 0)

        self.assertEqual(resultado["score"], 0)
        self.assertEqual(resultado["nivel_riesgo"], "alto")

    def test_limite_40_riesgo_alto(self):
        resultado = self.calcular(40, 40, 40, 40, 40)

        self.assertEqual(resultado["nivel_riesgo"], "alto")

    def test_limite_41_riesgo_medio(self):
        resultado = self.calcular(41, 41, 41, 41, 41)

        self.assertEqual(resultado["nivel_riesgo"], "medio")

    def test_limite_70_riesgo_medio(self):
        resultado = self.calcular(70, 70, 70, 70, 70)

        self.assertEqual(resultado["nivel_riesgo"], "medio")

    def test_limite_71_riesgo_bajo(self):
        resultado = self.calcular(71, 71, 71, 71, 71)

        self.assertEqual(resultado["nivel_riesgo"], "bajo")

    def test_streaming_no_evaluable(self):
        resultado = self.calcular(streaming=None)

        self.assertEqual(resultado["estado"], "no_evaluable")
        self.assertIsNone(resultado["score"])
        self.assertIn(
            "q_streaming",
            resultado["dimensiones_faltantes"],
        )

    def test_rechazar_booleanos(self):
        with self.assertRaises(ValueError):
            self.calcular(audio=False)

    def test_rechazar_puntaje_fuera_de_rango(self):
        with self.assertRaises(ValueError):
            self.calcular(consistencia=101)

    def test_resultado_determinista(self):
        self.assertEqual(
            self.calcular(),
            self.calcular(),
        )

    def test_presskit_con_campos_faltantes(self):
        resultado = calcular_score_viabilidad(
            q_audio=80,
            q_streaming={"q_streaming": 60},
            q_rrss={"q_rrss": 70},
            q_presskit={
                "q_presskit": None,
                "campos_obligatorios_faltantes": [
                    "biografia"
                ],
            },
            q_consistencia={"q_consistencia": 100},
        )

        self.assertIsNone(resultado["score"])
        self.assertIn(
            "biografia",
            resultado["motivos_no_evaluable"][0],
        )

    def test_consistencia_sin_verificacion(self):
        resultado = calcular_score_viabilidad(
            q_audio=80,
            q_streaming={"q_streaming": 60},
            q_rrss={"q_rrss": 70},
            q_presskit={"q_presskit": 90},
            q_consistencia={
                "q_consistencia": None,
                "criterios_no_evaluables": [
                    "identidad_musicbrainz"
                ],
            },
        )

        self.assertIsNone(resultado["score"])
        self.assertIn(
            "identidad_musicbrainz",
            resultado["motivos_no_evaluable"][0],
        )


if __name__ == "__main__":
    unittest.main()
