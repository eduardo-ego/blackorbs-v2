#!/usr/bin/env python3
"""Genera B_fig8_serie_completa.png: dos paneles (temperatura, humedad) de todo el
periodo, brechas > 3 min marcadas en gris. Requiere: pandas, matplotlib.
Usa B_lecturas.csv y B_brechas.csv (ejecutar B_lecturas.py y B_brechas.py antes).
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "B_lecturas.csv"
BRECHAS_CSV = AQUI / "B_brechas.csv"
SALIDA = AQUI / "B_fig8_serie_completa.png"


def main():
    df = pd.read_csv(CSV, parse_dates=["timestamp"]).sort_values("timestamp")
    brechas = pd.read_csv(BRECHAS_CSV, parse_dates=["inicio", "fin"])

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(6.5, 3.5), dpi=300)

    ax1.plot(df["timestamp"], df["temperature"], color="tab:red", linewidth=0.5)
    ax1.set_ylabel("Temperatura (°C)")

    ax2.plot(df["timestamp"], df["humidity"], color="tab:blue", linewidth=0.5)
    ax2.set_ylabel("Humedad (%HR)")
    ax2.set_xlabel("Fecha")

    for _, b in brechas.iterrows():
        ax1.axvspan(b["inicio"], b["fin"], color="gray", alpha=0.4, linewidth=0)
        ax2.axvspan(b["inicio"], b["fin"], color="gray", alpha=0.4, linewidth=0)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b-%d"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(SALIDA, dpi=300)
    print(f"-> {SALIDA}")


if __name__ == "__main__":
    main()
