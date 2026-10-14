#!/usr/bin/env python3
"""Genera B_resumen_dataset.md a partir de B_lecturas.csv.
Requiere: pandas, numpy. Ejecutar B_lecturas.py primero.
"""
import pandas as pd
import numpy as np
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "B_lecturas.csv"
SALIDA = AQUI / "B_resumen_dataset.md"


def stats(serie):
    return {
        "media": serie.mean(),
        "std": serie.std(ddof=1),
        "min": serie.min(),
        "max": serie.max(),
        "p5": serie.quantile(0.05),
        "p50": serie.quantile(0.50),
        "p95": serie.quantile(0.95),
    }


def main():
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    primera = df["timestamp"].iloc[0]
    ultima = df["timestamp"].iloc[-1]
    dias = (ultima - primera).total_seconds() / 86400.0

    diffs = df["timestamp"].diff().dropna().dt.total_seconds()
    intervalo_mediana_s = diffs.median()

    temp = stats(df["temperature"].dropna())
    hum = stats(df["humidity"].dropna())

    def fila(nombre, d):
        return (f"| {nombre} | {d['media']:.2f} | {d['std']:.2f} | {d['min']:.2f} | "
                f"{d['max']:.2f} | {d['p5']:.2f} | {d['p50']:.2f} | {d['p95']:.2f} |")

    contenido = f"""# B2 — Resumen del dataset (`lecturas`, device_id=ORBE_001)

- Primera lectura: **{primera.isoformat()}**
- Última lectura: **{ultima.isoformat()}**
- Total de lecturas: **{len(df)}**
- Días de operación (última - primera): **{dias:.2f} días**
- Intervalo de muestreo efectivo (mediana de diferencias entre timestamps consecutivos):
  **{intervalo_mediana_s:.1f} s** (nominal configurado: 60 s, ver `A_parametros_ml.md`)

> Nota: "días de operación" aquí es el rango temporal cubierto por timestamps, no tiempo con el
> sensor efectivamente reportando sin interrupciones — ver `B_brechas.csv`/`B_brechas.md` para el
> uptime real.

## Estadística descriptiva

| Variable | Media | Desv. std | Mín | Máx | P5 | P50 | P95 |
|---|---|---|---|---|---|---|---|
{fila("Temperatura (°C)", temp)}
{fila("Humedad (%HR)", hum)}

(Desviación estándar muestral, ddof=1. Calculado sobre valores no nulos únicamente.)
"""
    SALIDA.write_text(contenido)
    print(f"-> {SALIDA}")


if __name__ == "__main__":
    main()
