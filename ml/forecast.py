"""
Forecasting de temperatura/humedad.

Con poco historial usa un pronóstico "ingenuo" (persistencia: el futuro se
parece al presente). Con suficiente historial usa suavizado exponencial de
Holt (tendencia amortiguada) vía statsmodels, que captura si la variable está
subiendo/bajando de forma sostenida.
"""

import warnings
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from config import HORIZONTE_MINUTOS

MIN_PUNTOS_HOLT = 30


def _intervalo_minutos(df):
    if len(df) < 2:
        return 10.0
    diffs = df["timestamp"].diff().dropna().dt.total_seconds() / 60.0
    mediana = diffs.median()
    return float(mediana) if mediana and mediana > 0 else 10.0


def _forecast_variable(serie, pasos, minimo_puntos):
    serie = serie.dropna()
    if len(serie) == 0:
        return None, True

    if len(serie) < minimo_puntos:
        return float(serie.iloc[-1]), True  # persistencia, confianza baja

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            modelo = ExponentialSmoothing(
                serie.values, trend="add", damped_trend=True, initialization_method="estimated"
            ).fit()
        prediccion = modelo.forecast(pasos)
        return float(prediccion[-1]), False
    except Exception:
        return float(serie.iloc[-1]), True


def generar_forecast(df):
    if df.empty:
        return {
            "forecast_temperature": None,
            "forecast_humidity": None,
            "forecast_horizon_minutes": None,
            "confianza_baja": True,
        }

    intervalo = _intervalo_minutos(df)
    pasos = max(1, round(HORIZONTE_MINUTOS / intervalo))
    horizonte_minutos = round(intervalo * pasos)

    # Extrapolar muchos pasos hacia adelante exige más respaldo histórico que
    # extrapolar solo unos pocos: pedimos al menos el doble de puntos que de
    # pasos a pronosticar (con un piso de MIN_PUNTOS_HOLT) antes de decir
    # "confianza alta" en un horizonte largo como 60 min.
    minimo_puntos = max(MIN_PUNTOS_HOLT, pasos * 2)

    temp, temp_baja = _forecast_variable(df["temperature"], pasos, minimo_puntos)
    hum, hum_baja = _forecast_variable(df["humidity"], pasos, minimo_puntos)

    return {
        "forecast_temperature": round(temp, 2) if temp is not None else None,
        "forecast_humidity": round(hum, 2) if hum is not None else None,
        "forecast_horizon_minutes": horizonte_minutos,
        "confianza_baja": bool(temp_baja or hum_baja),
    }
