
import unittest

from app.services.viability_service import (
    calcular_q_audio_postulacion,
    calcular_q_streaming,
)


class TestCalcularQAudioPostulacion(unittest.TestCase):

    def crear_demo(self, puntaje, valido=True):
        return {
            "validacion_tecnica": {
                "valido": valido,
                "q_audio": puntaje,
            }
        }

    def test_una_demo(self):
        demos = [self.crear_demo(85)]

        self.assertEqual(
            calcular_q_audio_postulacion(demos),
            85,
        )

    def test_seleccionar_puntaje_maximo(self):
        demos = [
            self.crear_demo(85),
            self.crear_demo(100),
            self.crear_demo(80),
        ]

        self.assertEqual(
            calcular_q_audio_postulacion(demos),
            100,
        )

    def test_agregar_demo_inferior_no_reduce_puntaje(self):
        demos_originales = [
            self.crear_demo(95),
            self.crear_demo(80),
        ]

        demos_ampliadas = demos_originales + [
            self.crear_demo(40),
        ]

        self.assertEqual(
            calcular_q_audio_postulacion(demos_originales),
            calcular_q_audio_postulacion(demos_ampliadas),
        )

    def test_ignorar_demo_invalida(self):
        demos = [
            self.crear_demo(85),
            self.crear_demo(100, valido=False),
        ]

        self.assertEqual(
            calcular_q_audio_postulacion(demos),
            85,
        )

    def test_sin_demos(self):
        self.assertIsNone(
            calcular_q_audio_postulacion([])
        )

    def test_sin_demos_validas(self):
        demos = [
            self.crear_demo(80, valido=False),
        ]

        self.assertIsNone(
            calcular_q_audio_postulacion(demos)
        )

    def test_rechazar_puntaje_fuera_de_rango(self):
        demos = [self.crear_demo(120)]

        with self.assertRaises(ValueError):
            calcular_q_audio_postulacion(demos)

    def test_rechazar_puntaje_no_entero(self):
        demos = [self.crear_demo(85.5)]

        with self.assertRaises(ValueError):
            calcular_q_audio_postulacion(demos)


if __name__ == "__main__":
    unittest.main()


class TestCalcularQStreaming(unittest.TestCase):


    def crear_metricas(self, oyentes, reproducciones):
        return {
            "oyentes_acumulados": oyentes,
            "reproducciones_acumuladas": reproducciones,
        }

    def test_banda_emergente_con_alta_fidelidad(self):
        resultado = calcular_q_streaming(
            self.crear_metricas(800, 16000),
            identidad_confirmada=True,
        )

        self.assertEqual(resultado["puntaje_audiencia"], 20)
        self.assertEqual(resultado["puntaje_fidelidad"], 50)
        self.assertEqual(resultado["q_streaming"], 70)
        self.assertEqual(
            resultado["ratio_reproducciones_oyente"],
            20.0,
        )

    def test_banda_con_muchos_oyentes_y_baja_fidelidad(self):
        resultado = calcular_q_streaming(
            self.crear_metricas(6000, 7200),
            identidad_confirmada=True,
        )

        self.assertEqual(resultado["puntaje_audiencia"], 40)
        self.assertEqual(resultado["puntaje_fidelidad"], 10)
        self.assertEqual(resultado["q_streaming"], 50)

    def test_sin_oyentes(self):
        resultado = calcular_q_streaming(
            self.crear_metricas(0, 0),
            identidad_confirmada=True,
        )

        self.assertEqual(resultado["q_streaming"], 0)
        self.assertEqual(resultado["puntaje_fidelidad"], 0)

    def test_identidad_no_confirmada(self):
        resultado = calcular_q_streaming(
            self.crear_metricas(800, 16000),
            identidad_confirmada=False,
        )

        self.assertIsNone(resultado)

    def test_rechazar_metricas_negativas(self):
        with self.assertRaises(ValueError):
            calcular_q_streaming(
                self.crear_metricas(-100, 500),
                identidad_confirmada=True,
            )

    def test_rechazar_metricas_no_enteras(self):
        with self.assertRaises(ValueError):
            calcular_q_streaming(
                self.crear_metricas(800, 1500.5),
                identidad_confirmada=True,
            )

    def test_perfil_lastfm_no_encontrado(self):
        resultado = calcular_q_streaming(
            metricas=None,
            identidad_confirmada=False,
            perfil_encontrado=False,
        )

        self.assertEqual(resultado["q_streaming"], 0)
        self.assertEqual(resultado["puntaje_audiencia"], 0)
        self.assertEqual(resultado["puntaje_fidelidad"], 0)
