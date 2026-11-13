
import unittest

from app.services.viability_service import calcular_q_presskit


BASE = {
    "nombre_artistico": "Banda Ejemplo",
    "correo_contacto": "contacto@ejemplo.cl",
    "pais": "Chile",
    "tipo_proyecto": "Banda",
    "generos": ["Thrash Metal"],
    "biografia": (
        "Una banda de Santiago con material propio "
        "y muchas canciones."
    ),
}


class TestCalcularQPresskit(unittest.TestCase):

    def test_campos_obligatorios_completos(self):
        resultado = calcular_q_presskit(BASE)

        self.assertEqual(resultado["estado"], "evaluable")
        self.assertEqual(resultado["q_presskit"], 60)

    def test_presskit_completo(self):
        datos = {
            **BASE,
            "ciudad": "Santiago",
            "anio_inicio": 2018,
            "mensaje_sello": "Queremos grabar con ustedes.",
            "biografia": "X" * 350,
        }

        resultado = calcular_q_presskit(datos)

        self.assertEqual(resultado["q_presskit"], 100)

    def test_biografia_150_caracteres(self):
        datos = {**BASE, "biografia": "X" * 150}

        resultado = calcular_q_presskit(datos)

        self.assertEqual(
            resultado["desglose"]["bono_biografia"],
            7,
        )
        self.assertEqual(resultado["q_presskit"], 67)

    def test_biografia_349_caracteres(self):
        datos = {**BASE, "biografia": "X" * 349}

        resultado = calcular_q_presskit(datos)

        self.assertEqual(
            resultado["desglose"]["bono_biografia"],
            7,
        )

    def test_biografia_350_caracteres(self):
        datos = {**BASE, "biografia": "X" * 350}

        resultado = calcular_q_presskit(datos)

        self.assertEqual(
            resultado["desglose"]["bono_biografia"],
            15,
        )
        self.assertEqual(resultado["q_presskit"], 75)

    def test_generos_obligatorios_faltantes(self):
        datos = {**BASE, "generos": []}

        resultado = calcular_q_presskit(datos)

        self.assertEqual(
            resultado["estado"],
            "no_evaluable",
        )
        self.assertIsNone(resultado["q_presskit"])
        self.assertIn(
            "generos",
            resultado["campos_obligatorios_faltantes"],
        )

    def test_presskit_inexistente(self):
        resultado = calcular_q_presskit(None)

        self.assertIsNone(resultado["q_presskit"])
        self.assertEqual(
            len(resultado["campos_obligatorios_faltantes"]),
            6,
        )

    def test_anio_booleano_no_otorga_puntos(self):
        datos = {**BASE, "anio_inicio": True}

        resultado = calcular_q_presskit(datos)

        self.assertEqual(
            resultado["desglose"]["anio_inicio"],
            0,
        )

    def test_anio_futuro_no_otorga_puntos(self):
        datos = {**BASE, "anio_inicio": 2100}

        resultado = calcular_q_presskit(datos)

        self.assertEqual(
            resultado["desglose"]["anio_inicio"],
            0,
        )

    def test_ignorar_espacios_externos_biografia(self):
        datos = {
            **BASE,
            "biografia": "   " + ("X" * 150) + "  ",
        }

        resultado = calcular_q_presskit(datos)

        self.assertEqual(
            resultado["caracteres_biografia"],
            150,
        )

    def test_mensaje_vacio_no_otorga_puntos(self):
        datos = {**BASE, "mensaje_sello": "   "}

        resultado = calcular_q_presskit(datos)

        self.assertEqual(
            resultado["desglose"]["mensaje_sello"],
            0,
        )

    def test_biografia_inferior_minimo(self):
        datos = {**BASE, "biografia": "Corta"}

        resultado = calcular_q_presskit(datos)

        self.assertIsNone(resultado["q_presskit"])
        self.assertIn(
            "biografia",
            resultado["campos_obligatorios_faltantes"],
        )


if __name__ == "__main__":
    unittest.main()
