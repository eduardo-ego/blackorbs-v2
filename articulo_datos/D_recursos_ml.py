#!/usr/bin/env python3
"""D4 — Consumo de recursos del servicio blackorbs-v2-ml (proceso real en producción,
CM5) durante ~10 ciclos, más el tiempo de entrenamiento de Isolation Forest sobre el
dataset actual. Solo lectura: usa psutil sobre el proceso ya corriendo (systemd), no lo
reinicia ni lo modifica. Salida: D_recursos_ml.md, D_recursos_ml_muestras.csv.
Requiere: psutil, pandas, numpy, scikit-learn (para medir fit() con el código real).
"""
import subprocess
import sys
import time
from pathlib import Path

import psutil
import pandas as pd
import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "ml"))

CICLO_SEGUNDOS = 60
N_CICLOS = 10
INTERVALO_MUESTREO_S = 2.0

SALIDA_MD = AQUI / "D_recursos_ml.md"
SALIDA_CSV = AQUI / "D_recursos_ml_muestras.csv"


def pid_servicio_ml():
    out = subprocess.run(
        ["systemctl", "show", "blackorbs-v2-ml", "-p", "MainPID"],
        capture_output=True, text=True,
    ).stdout.strip()
    pid = int(out.split("=")[1])
    if pid == 0:
        raise RuntimeError("blackorbs-v2-ml no está corriendo (MainPID=0)")
    return pid


def medir_proceso(duracion_s):
    pid = pid_servicio_ml()
    proc = psutil.Process(pid)
    proc.cpu_percent(interval=None)  # descarta la primera lectura (siempre 0)

    muestras = []
    t_fin = time.monotonic() + duracion_s
    while time.monotonic() < t_fin:
        try:
            cpu = proc.cpu_percent(interval=None)
            mem = proc.memory_info()
            muestras.append({
                "t": time.time(), "cpu_pct": cpu,
                "rss_mb": mem.rss / (1024 * 1024), "vms_mb": mem.vms / (1024 * 1024),
            })
        except psutil.NoSuchProcess:
            break
        time.sleep(INTERVALO_MUESTREO_S)
    return pid, pd.DataFrame(muestras)


def medir_entrenamiento_if():
    """Tiempo de fit() de Isolation Forest con el código real sobre el dataset actual
    (hasta 2000 lecturas, igual que en producción vía ml/db.py::cargar_lecturas)."""
    from db import cargar_lecturas
    from config import DEVICE_ID, VARIABLES
    from sklearn.ensemble import IsolationForest

    df = cargar_lecturas(DEVICE_ID)
    datos = df[VARIABLES].dropna()

    tiempos = []
    for _ in range(5):
        modelo = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
        t0 = time.perf_counter()
        modelo.fit(datos.values)
        tiempos.append(time.perf_counter() - t0)

    return len(datos), tiempos


def main():
    duracion_s = CICLO_SEGUNDOS * N_CICLOS
    print(f"Midiendo proceso blackorbs-v2-ml durante {duracion_s}s (~{N_CICLOS} ciclos)...")
    pid, muestras = medir_proceso(duracion_s)
    muestras.to_csv(SALIDA_CSV, index=False)

    print("Midiendo tiempo de entrenamiento de Isolation Forest (5 repeticiones)...")
    n_datos, tiempos_fit = medir_entrenamiento_if()

    cpu_media = muestras["cpu_pct"].mean() if not muestras.empty else float("nan")
    cpu_max = muestras["cpu_pct"].max() if not muestras.empty else float("nan")
    rss_media = muestras["rss_mb"].mean() if not muestras.empty else float("nan")
    rss_max = muestras["rss_mb"].max() if not muestras.empty else float("nan")

    md = f"""# D4 — Consumo de recursos del servicio ML (proceso real, PID {pid})

Medido con `psutil` sobre el proceso ya corriendo bajo systemd (`blackorbs-v2-ml`, sin
reiniciarlo), muestreando cada {INTERVALO_MUESTREO_S:.0f} s durante {duracion_s} s
(~{N_CICLOS} ciclos de {CICLO_SEGUNDOS} s). {len(muestras)} muestras tomadas.

| Métrica | Media | Máximo |
|---|---|---|
| CPU (%) | {cpu_media:.2f} | {cpu_max:.2f} |
| RSS (MB) | {rss_media:.1f} | {rss_max:.1f} |

(CPU % es relativo a un núcleo, como lo reporta `psutil.Process.cpu_percent`; en un ciclo
de {CICLO_SEGUNDOS}s el proceso está dormido la mayor parte del tiempo entre ejecuciones de
`ejecutar_ciclo()`, así que el promedio incluye tiempo ocioso.)

## Tiempo de entrenamiento de Isolation Forest (código real, dataset actual)

- Tamaño del dataset de entrenamiento: {n_datos} lecturas (temperature+humidity sin NaN,
  hasta el límite de 2000 que usa `ml/db.py::cargar_lecturas` en producción).
- 5 repeticiones de `IsolationForest(n_estimators=200, contamination='auto',
  random_state=42).fit(...)`: {', '.join(f'{t*1000:.1f} ms' for t in tiempos_fit)}
- Media: {np.mean(tiempos_fit)*1000:.1f} ms, máximo: {np.max(tiempos_fit)*1000:.1f} ms.

Muestras crudas de CPU/RAM: `D_recursos_ml_muestras.csv`.
"""
    SALIDA_MD.write_text(md)
    print(f"-> {SALIDA_MD}\n-> {SALIDA_CSV}")


if __name__ == "__main__":
    main()
