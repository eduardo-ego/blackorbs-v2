import os

DEVICE_ID = os.environ.get("DEVICE_ID", "ORBE_001")
SQLITE_PATH = os.environ.get("SQLITE_PATH", "/home/blackorbs/blackorbs-v2/data/blackorbs.db")
API_URL = os.environ.get("ML_API_URL", "http://localhost:3001")

# Cada cuánto corre un ciclo de análisis.
CICLO_SEGUNDOS = int(os.environ.get("ML_CICLO_SEGUNDOS", "60"))

# Mínimo de lecturas históricas antes de confiar en Isolation Forest / Holt-Winters
# en vez de los métodos estadísticos simples (EWMA / persistencia).
MIN_LECTURAS_MODELO_APRENDIDO = 200

# A cuántos minutos hacia adelante se pronostica. Se convierte a "pasos" en
# tiempo real dividiendo entre el intervalo real entre lecturas (ver forecast.py),
# así que si el sensor cambia de frecuencia el horizonte en minutos no se mueve.
HORIZONTE_MINUTOS = int(os.environ.get("ML_HORIZONTE_MINUTOS", "60"))

# El sensor físico conectado es un SHT85 (temperatura + humedad); no mide presión.
VARIABLES = ["temperature", "humidity"]
