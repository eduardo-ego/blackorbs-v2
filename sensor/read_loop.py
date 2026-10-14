"""
Lector de sensor para v2.

El hardware conectado a este dispositivo es un SHT85 (temperatura + humedad,
dirección I2C 0x44) — no un BME680. Se confirmó escaneando el bus I2C real
antes de escribir este script (había un BME680 en el código v1, pero no
corresponde al sensor físico actual). Por eso no hay lectura de presión.
"""

import os
import json
import time
import logging
import statistics

import smbus2
import requests

from config import I2C_BUS, DEVICE_ADDR, API_URL, INTERVALO_SEGUNDOS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [sensor] %(message)s")
log = logging.getLogger("blackorbs-sensor")

CALIBRACION_PATH = os.path.join(os.path.dirname(__file__), "calibration.json")


def cargar_calibracion():
    """Se relee en cada ciclo para poder ajustar el offset sin reiniciar el servicio."""
    try:
        with open(CALIBRACION_PATH) as f:
            cal = json.load(f)
        return float(cal.get("temperature_offset", 0.0)), float(cal.get("humidity_offset", 0.0))
    except Exception:
        log.exception("no se pudo leer calibration.json, usando offset 0.0")
        return 0.0, 0.0


def soft_reset(bus):
    bus.write_i2c_block_data(DEVICE_ADDR, 0x30, [0xA2])
    time.sleep(0.02)


def leer_sensor(muestras=5, delay=0.1):
    try:
        with smbus2.SMBus(I2C_BUS) as bus:
            temps, hums = [], []
            for _ in range(muestras):
                bus.write_i2c_block_data(DEVICE_ADDR, 0x2C, [0x06])
                time.sleep(0.015)
                data = bus.read_i2c_block_data(DEVICE_ADDR, 0x00, 6)

                temp_raw = (data[0] << 8) + data[1]
                hum_raw = (data[3] << 8) + data[4]

                temps.append(-45 + 175 * (temp_raw / 65535.0))
                hums.append(100 * (hum_raw / 65535.0))
                time.sleep(delay)

        return statistics.mean(temps), statistics.mean(hums)
    except Exception:
        log.exception("error leyendo el sensor SHT85")
        return None, None


def enviar(temp, hum):
    payload = {"temperature": round(temp, 2), "humidity": round(hum, 2)}
    try:
        resp = requests.post(API_URL, json=payload, timeout=10)
        resp.raise_for_status()
        log.info("lectura enviada: %s", payload)
    except requests.RequestException:
        log.exception("no se pudo enviar la lectura a la API")


def main():
    with smbus2.SMBus(I2C_BUS) as bus:
        soft_reset(bus)
    time.sleep(0.5)

    log.info("lector de sensor iniciado, ciclo cada %ss hacia %s", INTERVALO_SEGUNDOS, API_URL)
    while True:
        temp, hum = leer_sensor()
        if None not in (temp, hum):
            offset_temp, offset_hum = cargar_calibracion()
            enviar(temp + offset_temp, hum + offset_hum)
        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()
