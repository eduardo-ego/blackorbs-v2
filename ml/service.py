import time
import logging

import requests

from config import DEVICE_ID, API_URL, CICLO_SEGUNDOS
from db import cargar_lecturas
from anomaly import detectar_anomalia, evaluar_valor_futuro, peor_mood
from forecast import generar_forecast

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ml] %(message)s")
log = logging.getLogger("blackorbs-ml")


def ejecutar_ciclo():
    df = cargar_lecturas(DEVICE_ID)

    anomalia = detectar_anomalia(df)
    forecast = generar_forecast(df)

    mood_forecast = "happy"
    if not forecast["confianza_baja"]:
        mood_forecast_temp = evaluar_valor_futuro(df, "temperature", forecast["forecast_temperature"])
        mood_forecast_hum = evaluar_valor_futuro(df, "humidity", forecast["forecast_humidity"])
        mood_forecast = peor_mood(mood_forecast_temp, mood_forecast_hum)

    mood_final = peor_mood(anomalia["mood"], mood_forecast)

    mensaje = anomalia["message"]
    if mood_forecast != "happy" and anomalia["mood"] == "happy":
        mensaje = "The forecast anticipates conditions could go out of range soon."

    payload = {
        "mood": mood_final,
        "anomaly_score": anomalia["score"],
        "anomaly_variable": anomalia["variable"],
        "normalidad_pct": anomalia["normalidad"],
        "forecast_temperature": forecast["forecast_temperature"],
        "forecast_humidity": forecast["forecast_humidity"],
        "forecast_horizon_minutes": forecast["forecast_horizon_minutes"],
        "forecast_confianza": "low" if forecast["confianza_baja"] else "high",
        "message": mensaje,
    }

    try:
        resp = requests.post(f"{API_URL}/ml/update", json=payload, timeout=10)
        resp.raise_for_status()
        log.info("estado publicado: mood=%s (anomalia=%s via %s, forecast_baja_confianza=%s)",
                  mood_final, anomalia["mood"], anomalia["metodo"], forecast["confianza_baja"])
    except requests.RequestException as e:
        log.error("no se pudo publicar el estado en la API: %s", e)


def main():
    log.info("servicio de ML iniciado para device_id=%s, ciclo=%ss", DEVICE_ID, CICLO_SEGUNDOS)
    while True:
        try:
            ejecutar_ciclo()
        except Exception:
            log.exception("error en el ciclo de ML")
        time.sleep(CICLO_SEGUNDOS)


if __name__ == "__main__":
    main()
