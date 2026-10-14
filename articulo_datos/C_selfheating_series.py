#!/usr/bin/env python3
"""C2 — Exporta lecturas en ventana [-60, +60] min alrededor de cada transición
start/stop del servicio blackorbs-v2-display del 2026-08-23 (ver C1_transiciones_display.md).
Salida: C_selfheating_series.csv (con columna 'transicion' identificando a cuál pertenece
cada fila; una fila puede pertenecer a más de una ventana si se solapan).
Requiere: pandas.
"""
import pandas as pd
from pathlib import Path
from zoneinfo import ZoneInfo

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "B_lecturas.csv"
SALIDA = AQUI / "C_selfheating_series.csv"

TZ = ZoneInfo("America/Mexico_City")

# Timestamps de las transiciones documentadas en C1_transiciones_display.md (hora local).
TRANSICIONES = [
    ("t1_started_1617", "2026-08-23T16:17:28"),
    ("t2_stopped_1617", "2026-08-23T16:17:56"),
    ("t3_started_1617", "2026-08-23T16:17:56"),
    ("t4_stopped_1618", "2026-08-23T16:18:20"),
    ("t5_started_1618", "2026-08-23T16:18:20"),
    ("t6_stopped_1619", "2026-08-23T16:19:12"),
    ("t7_started_1619", "2026-08-23T16:19:12"),
    ("t8_stopped_1640", "2026-08-23T16:40:52"),
    ("t9_started_1659_postfix", "2026-08-23T16:59:27"),
]


def main():
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    piezas = []
    for nombre, ts_local in TRANSICIONES:
        centro = pd.Timestamp(ts_local, tz=TZ)
        ini = centro - pd.Timedelta(minutes=60)
        fin = centro + pd.Timedelta(minutes=60)
        ventana = df[(df["timestamp"] >= ini) & (df["timestamp"] <= fin)].copy()
        ventana["transicion"] = nombre
        ventana["t_transicion_local"] = centro.isoformat()
        ventana["offset_min"] = (ventana["timestamp"] - centro).dt.total_seconds() / 60.0
        piezas.append(ventana)

    resultado = pd.concat(piezas, ignore_index=True)
    resultado.to_csv(SALIDA, index=False)
    print(f"{len(resultado)} filas -> {SALIDA}")
    print(resultado.groupby("transicion").size())


if __name__ == "__main__":
    main()
