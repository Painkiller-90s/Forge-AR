
"""
Configuración de las consultas y reintentos de MusicBrainz.
"""

# Tiempo máximo de espera de cada petición HTTP.
MUSICBRAINZ_TIMEOUT_SECONDS = 15.0

# Intervalo mínimo entre peticiones a MusicBrainz.
MUSICBRAINZ_MIN_REQUEST_INTERVAL_SECONDS = 1.1

# Espera inicial entre reintentos.
MUSICBRAINZ_RETRY_INITIAL_DELAY_SECONDS = 1.0

# Espera máxima entre reintentos.
MUSICBRAINZ_RETRY_MAX_DELAY_SECONDS = 60.0

# Multiplicador para aumentar progresivamente la espera.
MUSICBRAINZ_RETRY_BACKOFF_MULTIPLIER = 2.0

# No existe un máximo de intentos.
# Los errores temporales se reintentan indefinidamente.
