#!/usr/bin/env python3
"""C4 — Serie de temperatura del 2026-08-23 (~16:00-17:20 local) con las transiciones
start/stop del display marcadas con líneas verticales. Salida: C_fig9_selfheating_serie.png
(300 dpi, 3.2 x 2.4 in). Requiere: pandas, matplotlib.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from zoneinfo import ZoneInfo

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "B_lecturas.csv"
SALIDA = AQUI / "C_fig9_selfheating_serie.png"
TZ = ZoneInfo("America/Mexico_City")

TRANSICIONES = [
    ("Start", "2026-08-23T16:17:28"),
    ("Stop", "2026-08-23T16:17:56"),
    ("Start", "2026-08-23T16:17:56"),
    ("Stop", "2026-08-23T16:18:20"),
    ("Start", "2026-08-23T16:18:20"),
    ("Stop", "2026-08-23T16:19:12"),
    ("Start", "2026-08-23T16:19:12"),
    ("Stop", "2026-08-23T16:40:52"),
    ("Start (fix)", "2026-08-23T16:59:27"),
]

VENTANA_INICIO = "2026-08-23T16:00:00"
VENTANA_FIN = "2026-08-23T17:20:00"


def main():
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    ini = pd.Timestamp(VENTANA_INICIO, tz=TZ)
    fin = pd.Timestamp(VENTANA_FIN, tz=TZ)
    sub = df[(df["timestamp"] >= ini) & (df["timestamp"] <= fin)]

    fig, ax = plt.subplots(figsize=(3.2, 2.4), dpi=300)
    ax.plot(sub["timestamp"], sub["temperature"], color="tab:red", linewidth=0.8)

    for _, ts_local in TRANSICIONES:
        t = pd.Timestamp(ts_local, tz=TZ)
        ax.axvline(t, color="gray", linestyle="--", linewidth=0.6)

    ax.set_ylabel("Temperatura (°C)", fontsize=7)
    ax.set_xlabel("Hora local", fontsize=7)
    ax.tick_params(labelsize=6)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=TZ))
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.savefig(SALIDA, dpi=300)
    print(f"-> {SALIDA} ({len(sub)} puntos)")


if __name__ == "__main__":
    main()
