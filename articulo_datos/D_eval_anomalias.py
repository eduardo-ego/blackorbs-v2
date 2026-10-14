#!/usr/bin/env python3
"""D1 — Evaluación offline del detector de anomalías (Tabla 3).

Compara, sobre segmentos normales de B_lecturas.csv con anomalías sintéticas
inyectadas:
  - Baseline A: umbral fijo (temperatura: 35 C, el mismo valor codificado en
    api/Controllers/alertController.js; humedad: no hay umbral configurado en
    ningún lado del backend, así que se usa +-2 sigma del dataset completo,
    igual que pide la instrucción para el caso "si no hay").
  - Baseline B: z-score rodante, ventana de 60 muestras, |z| >= 2.0 = anomalia.
  - Etapa 1 real (ml/anomaly.py::_detectar_ewma, importado tal cual, sin
    reimplementar).
  - Etapa 2 real (ml/anomaly.py::_detectar_isolation_forest, importado tal
    cual).

Familias de anomalias sinteticas (semilla fija, RNG = np.random.default_rng(42)):
  - escalones: +-2, +-4, +-8 C y +-5, +-10, +-20 %HR, sostenidos 20 muestras.
  - rampas: 0.05-0.5 C/min, 10-60 min de duracion, solo temperatura (unica
    variable para la que la instruccion da un rango en C/min).
  - picos: 1-3 muestras, misma magnitud que los escalones.

Salida: D_tabla3_anomalias.csv, D_tabla3_anomalias.md.

Requiere: pandas, numpy, scikit-learn (para importar ml/anomaly.py).
El import real de ml/anomaly.py se logra agregando ml/ a sys.path.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "ml"))

import config as ml_config          # ml/config.py
from anomaly import _detectar_ewma, _detectar_isolation_forest, VENTANA_EWMA  # ml/anomaly.py

CSV = AQUI / "B_lecturas.csv"
SALIDA_CSV = AQUI / "D_tabla3_anomalias.csv"
SALIDA_MD = AQUI / "D_tabla3_anomalias.md"
SALIDA_HANDOVER_MD = AQUI / "D_tabla3b_handover_if.md"

DB_PATH = RAIZ / "data" / "blackorbs.db"

SEMILLA = 42
N_POR_FAMILIA = 30
UMBRAL_FIJO_TEMP = 35.0   # api/Controllers/alertController.js: threshold codificado
VENTANA_ZSCORE_ROD = 60
Z_ROD_UMBRAL = 2.0
MAX_HIST_IF = 2000        # igual a ml/db.py::cargar_lecturas(limite=2000)

MAGNITUDES_TEMP = [2, 4, 8]
MAGNITUDES_HUM = [5, 10, 20]
DUR_ESCALON = 20           # muestras (~20 min a 60s/muestra)
RAMPA_TASAS = (0.05, 0.5)  # C/min
RAMPA_DUR_MIN = (10, 60)   # minutos
PICO_DUR = (1, 3)          # muestras


# --------------------------------------------------------------------------
# Carga y segmentos "normales" (sin alertas, sin brechas, muestreo regular)
# --------------------------------------------------------------------------

def cargar_datos():
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def cargar_timestamps_alertas():
    import sqlite3
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    ts = pd.read_sql_query("SELECT timestamp FROM alertas", conn)["timestamp"]
    conn.close()
    ts = pd.to_datetime(ts, utc=True)
    return ts


def marcar_normal(df, alertas_ts, buffer_alerta_min=5, buffer_gap_min=5, tol_regular_s=90):
    normal = pd.Series(True, index=df.index)

    diffs_s = df["timestamp"].diff().dt.total_seconds()
    normal &= (diffs_s.isna() | (diffs_s <= tol_regular_s))
    # también excluir la muestra siguiente a una brecha (dato irregular tras el hueco)
    normal &= diffs_s.shift(-1).isna() | (diffs_s.shift(-1) <= tol_regular_s)

    if len(alertas_ts) > 0:
        alertas_ts_sorted = alertas_ts.sort_values().to_numpy()
        buf = pd.Timedelta(minutes=buffer_alerta_min).to_numpy()
        t = df["timestamp"].to_numpy()
        idx = np.searchsorted(alertas_ts_sorted, t)
        cerca = np.zeros(len(t), dtype=bool)
        for offset in (-1, 0):
            j = np.clip(idx + offset, 0, len(alertas_ts_sorted) - 1)
            cerca |= np.abs(alertas_ts_sorted[j] - t) <= buf
        normal &= ~cerca

    return normal


def segmentos_normales(normal, longitud_min):
    segmentos = []
    inicio = None
    for i, val in enumerate(normal):
        if val and inicio is None:
            inicio = i
        elif not val and inicio is not None:
            if i - inicio >= longitud_min:
                segmentos.append((inicio, i))
            inicio = None
    if inicio is not None and len(normal) - inicio >= longitud_min:
        segmentos.append((inicio, len(normal)))
    return segmentos


# --------------------------------------------------------------------------
# Generación de anomalías sintéticas
# --------------------------------------------------------------------------

def generar_injecciones(df, rng, longitud_min_segmento=250):
    normal = marcar_normal(df, cargar_timestamps_alertas())
    segs = segmentos_normales(normal, longitud_min_segmento)
    if not segs:
        raise RuntimeError("No se encontraron segmentos normales suficientemente largos.")

    intervalo_s = df["timestamp"].diff().dt.total_seconds().median()
    injecciones = []

    def punto_aleatorio(margen_fin):
        seg = segs[rng.integers(0, len(segs))]
        ini, fin = seg
        # dejamos MIN_LECTURAS_MODELO_APRENDIDO de contexto real antes del punto,
        # y margen_fin muestras libres después para poder observar el efecto.
        lo = max(ini, ml_config.MIN_LECTURAS_MODELO_APRENDIDO + 10)
        hi = fin - margen_fin
        if hi <= lo:
            return None
        return int(rng.integers(lo, hi))

    # --- escalones ---
    for _ in range(N_POR_FAMILIA):
        i0 = None
        while i0 is None:
            i0 = punto_aleatorio(DUR_ESCALON + 30)
        var = rng.choice(["temperature", "humidity"])
        mags = MAGNITUDES_TEMP if var == "temperature" else MAGNITUDES_HUM
        mag = float(rng.choice(mags)) * float(rng.choice([1, -1]))
        injecciones.append({"familia": "escalon", "variable": var, "i0": i0,
                             "duracion": DUR_ESCALON, "magnitud": mag})

    # --- rampas (solo temperatura) ---
    for _ in range(N_POR_FAMILIA):
        dur_min = rng.uniform(*RAMPA_DUR_MIN)
        dur_muestras = max(2, int(round(dur_min * 60 / intervalo_s)))
        i0 = None
        while i0 is None:
            i0 = punto_aleatorio(dur_muestras + 30)
        tasa = rng.uniform(*RAMPA_TASAS) * float(rng.choice([1, -1]))
        injecciones.append({"familia": "rampa", "variable": "temperature", "i0": i0,
                             "duracion": dur_muestras, "magnitud": tasa * dur_min})
        injecciones[-1]["tasa_c_min"] = tasa

    # --- picos ---
    for _ in range(N_POR_FAMILIA):
        dur = int(rng.integers(PICO_DUR[0], PICO_DUR[1] + 1))
        i0 = None
        while i0 is None:
            i0 = punto_aleatorio(dur + 30)
        var = rng.choice(["temperature", "humidity"])
        mags = MAGNITUDES_TEMP if var == "temperature" else MAGNITUDES_HUM
        mag = float(rng.choice(mags)) * float(rng.choice([1, -1]))
        injecciones.append({"familia": "pico", "variable": var, "i0": i0,
                             "duracion": dur, "magnitud": mag})

    return injecciones


def aplicar_injeccion(df, inj):
    """Devuelve una copia de df con la anomalía aplicada, y el rango [i0, i0+dur) de verdad-base."""
    d = df.copy()
    i0, dur, var, fam = inj["i0"], inj["duracion"], inj["variable"], inj["familia"]

    if fam in ("escalon", "pico"):
        d.loc[i0:i0 + dur - 1, var] = d.loc[i0:i0 + dur - 1, var] + inj["magnitud"]
    elif fam == "rampa":
        tasa = inj["tasa_c_min"]
        intervalo_min = df["timestamp"].diff().dt.total_seconds().median() / 60.0
        incremento = np.arange(1, dur + 1) * tasa * intervalo_min
        d.loc[i0:i0 + dur - 1, var] = d.loc[i0:i0 + dur - 1, var].to_numpy() + incremento

    return d, (i0, i0 + dur)


# --------------------------------------------------------------------------
# Detectores
# --------------------------------------------------------------------------

def baseline_fijo(ventana_df, sigma_temp, sigma_hum, media_temp, media_hum):
    ultima = ventana_df.iloc[-1]
    anom_temp = ultima["temperature"] >= UMBRAL_FIJO_TEMP
    anom_hum = abs(ultima["humidity"] - media_hum) > 2 * sigma_hum
    return bool(anom_temp or anom_hum)


def baseline_zscore_rodante(ventana_df):
    if len(ventana_df) <= VENTANA_ZSCORE_ROD:
        return False
    ref = ventana_df.iloc[-(VENTANA_ZSCORE_ROD + 1):-1]
    ultima = ventana_df.iloc[-1]
    for var in ["temperature", "humidity"]:
        std = ref[var].std(ddof=0)
        if std == 0 or np.isnan(std):
            continue
        z = abs((ultima[var] - ref[var].mean()) / std)
        if z >= Z_ROD_UMBRAL:
            return True
    return False


def etapa1_real(ventana_df):
    r = _detectar_ewma(ventana_df)
    return r["mood"] != "contento"


def etapa2_real(ventana_df):
    r = _detectar_isolation_forest(ventana_df)
    if r is None:
        return None
    return r["mood"] != "contento"


# --------------------------------------------------------------------------
# Evaluación
# --------------------------------------------------------------------------

def evaluar_injeccion(df_original, inj, sigma_temp, sigma_hum, media_temp, media_hum,
                       tiempos_cpu):
    d, (gt_ini, gt_fin) = aplicar_injeccion(df_original, inj)
    k_max = (gt_fin - gt_ini) + 20  # ventana de observación: duración + margen post-anomalía

    resultados = {det: [] for det in ["fijo", "zscore_rodante", "etapa1", "etapa2"]}
    verdad = []

    for k in range(k_max):
        idx = gt_ini + k
        if idx >= len(d):
            break
        ini_ctx = max(0, idx + 1 - MAX_HIST_IF)
        ventana = d.iloc[ini_ctx:idx + 1].reset_index(drop=True)

        verdad.append(1 if gt_ini <= idx < gt_fin else 0)

        resultados["fijo"].append(baseline_fijo(ventana, sigma_temp, sigma_hum, media_temp, media_hum))
        resultados["zscore_rodante"].append(baseline_zscore_rodante(ventana))

        t0 = time.perf_counter()
        r1 = etapa1_real(ventana)
        tiempos_cpu["etapa1"].append(time.perf_counter() - t0)
        resultados["etapa1"].append(r1)

        t0 = time.perf_counter()
        r2 = etapa2_real(ventana)
        dt2 = time.perf_counter() - t0
        if r2 is not None:
            tiempos_cpu["etapa2"].append(dt2)
        resultados["etapa2"].append(r2)

    return verdad, resultados


def metricas(verdad, pred):
    pares = [(v, p) for v, p in zip(verdad, pred) if p is not None]
    if not pares:
        return None
    v = np.array([x[0] for x in pares])
    p = np.array([1 if x[1] else 0 for x in pares])

    tp = int(((v == 1) & (p == 1)).sum())
    fp = int(((v == 0) & (p == 1)).sum())
    fn = int(((v == 1) & (p == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
    recall = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 and not np.isnan(precision) and not np.isnan(recall)
          else float("nan")
          )

    primer_hit = None
    for i, (vv, pp) in enumerate(pares):
        if vv == 1:
            if pp == 1:
                primer_hit = i - next(j for j, (vv2, _) in enumerate(pares) if vv2 == 1)
            break
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def retardo_deteccion(verdad, pred):
    """Muestras desde el inicio de la anomalía real hasta la primera detección positiva."""
    verdad = np.array(verdad)
    idx_inicio = np.argmax(verdad == 1) if (verdad == 1).any() else None
    if idx_inicio is None:
        return None
    for k in range(idx_inicio, len(pred)):
        if pred[k]:
            return k - idx_inicio
    return None


def main():
    rng = np.random.default_rng(SEMILLA)
    df = cargar_datos()

    sigma_temp = df["temperature"].std(ddof=0)
    sigma_hum = df["humidity"].std(ddof=0)
    media_temp = df["temperature"].mean()
    media_hum = df["humidity"].mean()

    injecciones = generar_injecciones(df, rng)
    print(f"{len(injecciones)} inyecciones generadas "
          f"({sum(i['familia']=='escalon' for i in injecciones)} escalones, "
          f"{sum(i['familia']=='rampa' for i in injecciones)} rampas, "
          f"{sum(i['familia']=='pico' for i in injecciones)} picos)")

    tiempos_cpu = {"etapa1": [], "etapa2": []}
    filas = []
    for inj in injecciones:
        verdad, resultados = evaluar_injeccion(df, inj, sigma_temp, sigma_hum, media_temp, media_hum,
                                                tiempos_cpu)
        for detector, pred in resultados.items():
            m = metricas(verdad, pred)
            retardo = retardo_deteccion(verdad, pred)
            filas.append({
                "familia": inj["familia"], "variable": inj["variable"],
                "magnitud": inj.get("magnitud"), "duracion_muestras": inj["duracion"],
                "detector": detector,
                "precision": m["precision"] if m else np.nan,
                "recall": m["recall"] if m else np.nan,
                "f1": m["f1"] if m else np.nan,
                "retardo_muestras": retardo,
            })

    detalle = pd.DataFrame(filas)
    detalle_csv = AQUI / "D_tabla3_detalle_injecciones.csv"
    detalle.to_csv(detalle_csv, index=False)

    resumen = (
        detalle.groupby(["detector", "familia"])
        .agg(precision=("precision", "mean"), recall=("recall", "mean"), f1=("f1", "mean"),
             retardo_medio_muestras=("retardo_muestras", "mean"), n=("familia", "count"))
        .reset_index()
    )
    resumen["cpu_ms_por_ciclo"] = resumen["detector"].map({
        "fijo": 0.0,
        "zscore_rodante": 0.0,
        "etapa1": 1000 * np.mean(tiempos_cpu["etapa1"]) if tiempos_cpu["etapa1"] else np.nan,
        "etapa2": 1000 * np.mean(tiempos_cpu["etapa2"]) if tiempos_cpu["etapa2"] else np.nan,
    })
    resumen.to_csv(SALIDA_CSV, index=False)

    md = ["# D1 — Tabla 3: evaluación del detector de anomalías (offline, sintético)", "",
          f"Semilla fija: {SEMILLA}. {N_POR_FAMILIA} inyecciones por familia "
          f"(escalón, rampa, pico) = {3*N_POR_FAMILIA} inyecciones totales.",
          "",
          "Baseline A ('fijo'): temperatura >= 35 C (umbral codificado en "
          "api/Controllers/alertController.js); humedad: +-2 sigma del dataset completo "
          "(no hay umbral de humedad configurado en el backend).",
          "Baseline B ('zscore_rodante'): |z| >= 2.0 sobre ventana rodante de 60 muestras.",
          "'etapa1' y 'etapa2' llaman directamente a ml/anomaly.py::_detectar_ewma y "
          "_detectar_isolation_forest (código real, no reimplementado).",
          "",
          "| Detector | Familia | Precisión | Recall | F1 | Retardo medio (muestras) | N | CPU/ciclo (ms) |",
          "|---|---|---|---|---|---|---|---|"]
    for _, r in resumen.iterrows():
        md.append(f"| {r['detector']} | {r['familia']} | {r['precision']:.3f} | {r['recall']:.3f} | "
                   f"{r['f1']:.3f} | {r['retardo_medio_muestras']:.1f} | {int(r['n'])} | "
                   f"{r['cpu_ms_por_ciclo']:.2f} |")
    md.append("")
    md.append("Detalle por inyección individual: `D_tabla3_detalle_injecciones.csv`.")
    SALIDA_MD.write_text("\n".join(md) + "\n")
    print(f"-> {SALIDA_CSV}\n-> {SALIDA_MD}")

    # --- Handover: métricas de etapa 2 en función del tamaño de entrenamiento ---
    evaluar_handover_if(df, rng)


def evaluar_handover_if(df, rng, tamanos=(100, 200, 500, 1000), n_puntos=25):
    """Para justificar MIN_LECTURAS_MODELO_APRENDIDO=200: para cada tamaño de historial
    de entrenamiento, se toman n_puntos muestras normales al azar, se les inyecta un
    escalón de +4 C, y se mide si Isolation Forest (entrenado solo con las `tamano`
    lecturas previas) marca esa muestra como anomalía."""
    normal = marcar_normal(df, cargar_timestamps_alertas())
    idx_validos = [i for i in range(max(tamanos) + 10, len(df)) if normal[i]]
    if len(idx_validos) < n_puntos:
        idx_validos = list(range(max(tamanos) + 10, len(df)))

    filas = []
    for tamano in tamanos:
        elegidos = rng.choice(idx_validos, size=min(n_puntos, len(idx_validos)), replace=False)
        detectadas = 0
        normalidades = []
        for idx in elegidos:
            ventana = df.iloc[idx - tamano:idx].copy().reset_index(drop=True)
            fila_anom = df.iloc[[idx]].copy()
            fila_anom["temperature"] += 4.0
            ventana = pd.concat([ventana, fila_anom], ignore_index=True)
            r = _detectar_isolation_forest(ventana)
            if r is None:
                continue
            normalidades.append(r["normalidad"])
            if r["mood"] != "contento":
                detectadas += 1
        n_eval = len(normalidades)
        filas.append({
            "n_entrenamiento": tamano,
            "n_evaluados": n_eval,
            "tasa_deteccion_escalon_+4C": detectadas / n_eval if n_eval else np.nan,
            "normalidad_pct_media": float(np.mean(normalidades)) if normalidades else np.nan,
        })

    resumen = pd.DataFrame(filas)
    lineas = ["# D1b — Métricas de etapa 2 (Isolation Forest) vs. tamaño de entrenamiento", "",
              "Se inyecta un escalón fijo de +4 C sobre una lectura normal y se mide si "
              "Isolation Forest (entrenado solo con las N lecturas previas) lo marca como "
              "anómalo, para distintos N. Justifica el umbral "
              f"MIN_LECTURAS_MODELO_APRENDIDO={ml_config.MIN_LECTURAS_MODELO_APRENDIDO}.",
              "",
              "| N entrenamiento | N evaluados | Tasa detección escalón +4°C | Normalidad % media |",
              "|---|---|---|---|"]
    for _, r in resumen.iterrows():
        lineas.append(f"| {int(r['n_entrenamiento'])} | {int(r['n_evaluados'])} | "
                       f"{r['tasa_deteccion_escalon_+4C']:.2%} | {r['normalidad_pct_media']:.1f} |")
    SALIDA_HANDOVER_MD.write_text("\n".join(lineas) + "\n")
    print(f"-> {SALIDA_HANDOVER_MD}")


if __name__ == "__main__":
    main()
