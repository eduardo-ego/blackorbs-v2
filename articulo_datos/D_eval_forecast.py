#!/usr/bin/env python3
"""D2 — Evaluación rolling-origin del forecast (Tabla 4).

Compara, sobre B_lecturas.csv, el forecast real del sistema
(ml/forecast.py::generar_forecast, que internamente decide persistencia vs. Holt
damped según MIN_PUNTOS_HOLT) contra una baseline de persistencia pura (siempre
"el futuro = el presente", sin importar cuántos datos haya), usando el horizonte
real del sistema (HORIZONTE_MINUTOS = ml/config.py).

Metodología rolling-origin: para cada punto de origen i (con paso STRIDE para
mantener el tiempo de cómputo razonable), se llama a generar_forecast() con el
historial hasta i (capado a 2000 lecturas, igual que ml/db.py::cargar_lecturas
en producción) y se compara la predicción contra el valor real observado
`pasos` muestras después, siempre que ese punto futuro exista y no haya una
brecha > 3 min entre origen y destino.

Salida: D_tabla4_forecast.csv, D_tabla4_forecast.md.
Requiere: pandas, numpy, statsmodels (para importar ml/forecast.py).
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "ml"))

from config import HORIZONTE_MINUTOS       # ml/config.py
from forecast import generar_forecast, _intervalo_minutos  # ml/forecast.py

CSV = AQUI / "B_lecturas.csv"
SALIDA_CSV = AQUI / "D_tabla4_forecast.csv"
SALIDA_MD = AQUI / "D_tabla4_forecast.md"

MAX_HIST = 2000       # igual a ml/db.py::cargar_lecturas(limite=2000)
STRIDE = 20           # cada cuántas muestras se evalúa un origen (control de tiempo de cómputo)
MIN_HIST_INICIAL = 5  # no evaluar antes de tener al menos esto de historial
GAP_MAX_S = 180       # 3 min, igual criterio que B3


def cargar_datos():
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    return df.sort_values("timestamp").reset_index(drop=True)


def persistencia_pura(hist, pasos_ignorado=None):
    return {
        "forecast_temperature": float(hist["temperature"].iloc[-1]),
        "forecast_humidity": float(hist["humidity"].iloc[-1]),
    }


def main():
    df = cargar_datos()
    n = len(df)

    filas = []
    for i in range(MIN_HIST_INICIAL, n - 1, STRIDE):
        ini_hist = max(0, i + 1 - MAX_HIST)
        hist = df.iloc[ini_hist:i + 1].reset_index(drop=True)

        intervalo = _intervalo_minutos(hist)
        pasos = max(1, round(HORIZONTE_MINUTOS / intervalo))
        j = i + pasos
        if j >= n:
            continue

        # descartar si hay una brecha > GAP_MAX_S entre el origen y el destino
        sub_ts = df["timestamp"].iloc[i:j + 1]
        if sub_ts.diff().dt.total_seconds().max() > GAP_MAX_S:
            continue

        real_temp = df["temperature"].iloc[j]
        real_hum = df["humidity"].iloc[j]

        t0 = time.perf_counter()
        f_real = generar_forecast(hist)
        dt_holt = time.perf_counter() - t0

        f_persist = persistencia_pura(hist)

        filas.append({
            "i_origen": i, "j_destino": j, "pasos": pasos,
            "confianza_baja": f_real["confianza_baja"],
            "real_temperature": real_temp, "real_humidity": real_hum,
            "sistema_forecast_temperature": f_real["forecast_temperature"],
            "sistema_forecast_humidity": f_real["forecast_humidity"],
            "persistencia_forecast_temperature": f_persist["forecast_temperature"],
            "persistencia_forecast_humidity": f_persist["forecast_humidity"],
            "cpu_ms_sistema": dt_holt * 1000,
        })

    detalle = pd.DataFrame(filas)
    detalle_csv = AQUI / "D_tabla4_detalle_origenes.csv"
    detalle.to_csv(detalle_csv, index=False)

    def mae_rmse(real, pred):
        err = (real - pred).dropna()
        return float(err.abs().mean()), float(np.sqrt((err ** 2).mean()))

    filas_resumen = []
    for confianza_grupo in [None, True, False]:
        sub = detalle if confianza_grupo is None else detalle[detalle["confianza_baja"] == confianza_grupo]
        if sub.empty:
            continue
        etiqueta = "todos" if confianza_grupo is None else ("confianza_baja" if confianza_grupo else "confianza_alta")
        for var in ["temperature", "humidity"]:
            mae_s, rmse_s = mae_rmse(sub[f"real_{var}"], sub[f"sistema_forecast_{var}"])
            mae_p, rmse_p = mae_rmse(sub[f"real_{var}"], sub[f"persistencia_forecast_{var}"])
            filas_resumen.append({"grupo": etiqueta, "variable": var, "n": len(sub),
                                   "mae_sistema": mae_s, "rmse_sistema": rmse_s,
                                   "mae_persistencia": mae_p, "rmse_persistencia": rmse_p})

    resumen = pd.DataFrame(filas_resumen)
    resumen.to_csv(SALIDA_CSV, index=False)

    cpu_media_ms = detalle["cpu_ms_sistema"].mean()
    md = ["# D2 — Tabla 4: evaluación rolling-origin del forecast", "",
          f"Horizonte real del sistema: {HORIZONTE_MINUTOS} min "
          f"(HORIZONTE_MINUTOS en ml/config.py). Origen evaluado cada {STRIDE} muestras, "
          f"historial capado a {MAX_HIST} lecturas (igual que ml/db.py en producción).",
          f"'sistema' = ml/forecast.py::generar_forecast (código real, decide persistencia vs. "
          f"Holt damped según MIN_PUNTOS_HOLT). 'persistencia' = baseline naive pura (siempre "
          f"último valor observado), evaluada con el mismo horizonte en pasos.",
          f"Tiempo de CPU medio de generar_forecast(): {cpu_media_ms:.2f} ms/llamada "
          f"({len(detalle)} llamadas).",
          "",
          "| Grupo | Variable | N | MAE sistema | RMSE sistema | MAE persistencia | RMSE persistencia |",
          "|---|---|---|---|---|---|---|"]
    for _, r in resumen.iterrows():
        md.append(f"| {r['grupo']} | {r['variable']} | {int(r['n'])} | {r['mae_sistema']:.3f} | "
                   f"{r['rmse_sistema']:.3f} | {r['mae_persistencia']:.3f} | {r['rmse_persistencia']:.3f} |")
    md.append("")
    md.append("Detalle por origen individual: `D_tabla4_detalle_origenes.csv`.")
    SALIDA_MD.write_text("\n".join(md) + "\n")
    print(f"-> {SALIDA_CSV}\n-> {SALIDA_MD}  ({len(detalle)} orígenes evaluados)")


if __name__ == "__main__":
    main()
