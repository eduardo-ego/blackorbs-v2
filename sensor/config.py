import os

I2C_BUS = int(os.environ.get("SENSOR_I2C_BUS", "6"))
DEVICE_ADDR = int(os.environ.get("SENSOR_I2C_ADDR", "0x44"), 16)
API_URL = os.environ.get("SENSOR_API_URL", "http://localhost:3001/data")
INTERVALO_SEGUNDOS = int(os.environ.get("SENSOR_INTERVALO_SEGUNDOS", "60"))
