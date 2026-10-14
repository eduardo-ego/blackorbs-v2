#!/usr/bin/env python3
"""C3 — Media, desv. std, N y pendiente (°C/min) de temperatura por fase del
experimento de autocalentamiento (ver interpretación en C1_transiciones_display.md).
Salida: C_selfheating_tabla.md. Requiere: pandas, numpy.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from zoneinfo import ZoneInfo

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "B_lecturas.csv"
SALIDA = AQUI / "C_selfheating_tabla.md"
TZ = ZoneInfo("America/Mexico_City")

# Ventanas propuestas en C1_transiciones_display.md — ajustar aquí si el autor confirma otras.
FASES = [
    ("Línea base (display off)", "2026-08-23T16:02:28", "2026-08-23T16:17:28"),
    ("Animación continua (15 min)", "2026-08-23T16:19:12", "2026-08-23T16:34:12"),
    ("Tras detener (10 min)", "2026-08-23T16:40:52", "2026-08-23T16:50:52"),
    ("Duty-cycled post-corrección (15 min)", "2026-08-23T16:59:27", "2026-08-23T17:14:27"),
]


def pendiente_por_minuto(sub):
    """Regresión lineal simple temperatura ~ minutos desde el inicio de la ventana."""
    if len(sub) < 2:
        return np.nan
    t_min = (sub["timestamp"] - sub["timestamp"].iloc[0]).dt.total_seconds() / 60.0
    coef = np.polyfit(t_min, sub["temperature"], 1)
    return coef[0]  # °C / min


def main():
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    df = df.sort_values("timestamp")

    filas = []
    for nombre, ini_s, fin_s in FASES:
        ini = pd.Timestamp(ini_s, tz=TZ)
        fin = pd.Timestamp(fin_s, tz=TZ)
        sub = df[(df["timestamp"] >= ini) & (df["timestamp"] <= fin)]
        if sub.empty:
            filas.append((nombre, np.nan, np.nan, 0, np.nan))
            continue
        media = sub["temperature"].mean()
        std = sub["temperature"].std(ddof=1)
        n = len(sub)
        pendiente = pendiente_por_minuto(sub)
        filas.append((nombre, media, std, n, pendiente))

    lineas = [
        "# C3 — Autocalentamiento por fase (temperatura)",
        "",
        "Ventanas usadas (hora local America/Mexico_City) — ver justificación en",
        "`C1_transiciones_display.md`.",
        "",
        "| Fase | Media (°C) | Desv. std (°C) | N muestras | Pendiente (°C/min) |",
        "|---|---|---|---|---|",
    ]
    for nombre, media, std, n, pendiente in filas:
        m = f"{media:.2f}" if pd.notna(media) else "s/d"
        s = f"{std:.2f}" if pd.notna(std) else "s/d"
        p = f"{pendiente:+.3f}" if pd.notna(pendiente) else "s/d"
        lineas.append(f"| {nombre} | {m} | {s} | {n} | {p} |")

    lineas.append("")
    lineas.append(
        "Pendiente calculada por regresión lineal (mínimos cuadrados) de temperatura vs. "
        "minutos transcurridos dentro de cada ventana."
    )
    SALIDA.write_text("\n".join(lineas) + "\n")
    print(f"-> {SALIDA}")
    for f in filas:
        print(f)


if __name__ == "__main__":
    main()
