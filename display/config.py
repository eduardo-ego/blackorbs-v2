import os

DEVICE_ID = os.environ.get("DEVICE_ID", "ORBE_001")
SQLITE_PATH = os.environ.get("SQLITE_PATH", "/home/blackorbs/blackorbs-v2/data/blackorbs.db")

I2C_BUS = int(os.environ.get("DISPLAY_I2C_BUS", "6"))
I2C_ADDR = int(os.environ.get("DISPLAY_I2C_ADDR", "0x3C"), 16)

# Cada cuánto se despierta, dibuja UN frame y vuelve a dormir. Igualado al
# intervalo del sensor (60s) a propósito: se midió que animar continuamente
# calentaba el sensor ~1-2°C por carga sostenida de CPU, así que aquí el
# proceso pasa casi todo el tiempo dormido en vez de en un loop de animación.
REFRESCO_SEGUNDOS = int(os.environ.get("DISPLAY_REFRESCO_SEGUNDOS", "60"))
