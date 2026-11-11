
import unittest

from app.services.audio_validation_service import calcular_q_audio


class TestCalcularQAudio(unittest.TestCase):

    def test_flac_16_bits_44100_hz(self):
        resultado = calcular_q_audio(
            "flac", 44100, None, 16
        )
        self.assertEqual(resultado, 85)

    def test_flac_24_bits_96000_hz(self):
        resultado = calcular_q_audio(
            "flac", 96000, None, 24
        )
        self.assertEqual(resultado, 100)

    def test_mp3_128_kbps_44100_hz(self):
        resultado = calcular_q_audio(
            "mp3", 44100, 128000, None
        )
        self.assertEqual(resultado, 50)

    def test_mp3_192_kbps_44100_hz(self):
        resultado = calcular_q_audio(
            "mp3", 44100, 192000, None
        )
        self.assertEqual(resultado, 65)

    def test_mp3_320_kbps_44100_hz(self):
        resultado = calcular_q_audio(
            "mp3", 44100, 320000, None
        )
        self.assertEqual(resultado, 80)

    def test_mp3_320_kbps_48000_hz(self):
        resultado = calcular_q_audio(
            "mp3", 48000, 320000, None
        )
        self.assertEqual(resultado, 85)

    def test_flac_16_bits_48000_hz(self):
        resultado = calcular_q_audio(
            "flac", 48000, None, 16
        )
        self.assertEqual(resultado, 90)

    def test_rechazar_frecuencia_inferior_minima(self):
        with self.assertRaises(ValueError):
            calcular_q_audio(
                "flac", 22050, None, 16
            )

    def test_rechazar_mp3_inferior_128_kbps(self):
        with self.assertRaises(ValueError):
            calcular_q_audio(
                "mp3", 44100, 96000, None
            )

    def test_rechazar_flac_inferior_16_bits(self):
        with self.assertRaises(ValueError):
            calcular_q_audio(
                "flac", 44100, None, 8
            )

    def test_rechazar_mp3_sin_bitrate(self):
        with self.assertRaises(ValueError):
            calcular_q_audio(
                "mp3", 44100, None, None
            )

    def test_rechazar_flac_sin_profundidad(self):
        with self.assertRaises(ValueError):
            calcular_q_audio(
                "flac", 44100, None, None
            )

    def test_rechazar_formato_no_compatible(self):
        with self.assertRaises(ValueError):
            calcular_q_audio(
                "wav", 44100, None, None
            )


if __name__ == "__main__":
    unittest.main()
