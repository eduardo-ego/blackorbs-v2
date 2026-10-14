#!/usr/bin/env python3
"""Detecta huecos > 3 minutos en B_lecturas.csv y calcula uptime %.
Genera B_brechas.csv y B_brechas.md. Requiere: pandas.
"""
import pandas as pd
from pathlib import Path
from zoneinfo import ZoneInfo

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "B_lecturas.csv"
SALIDA_CSV = AQUI / "B_brechas.csv"
SALIDA_MD = AQUI / "B_brechas.md"

UMBRAL_MIN = 3.0
TZ_LOCAL = ZoneInfo("America/Mexico_City")


def main():
    df = pd.read_csv(CSV, parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    ts = df["timestamp"].dt.tz_localize("UTC") if df["timestamp"].dt.tz is None else df["timestamp"]

    diffs = ts.diff()
    huecos = []
    for i in range(1, len(ts)):
        dur = diffs.iloc[i].total_seconds() / 60.0
        if dur > UMBRAL_MIN:
            huecos.append({
                "inicio": ts.iloc[i - 1].isoformat(),
                "fin": ts.iloc[i].isoformat(),
                "inicio_local": ts.iloc[i - 1].tz_convert(TZ_LOCAL).isoformat(),
                "fin_local": ts.iloc[i].tz_convert(TZ_LOCAL).isoformat(),
                "duracion_min": round(dur, 2),
            })

    brechas_df = pd.DataFrame(huecos)
    brechas_df.to_csv(SALIDA_CSV, index=False)

    tiempo_total_min = (ts.iloc[-1] - ts.iloc[0]).total_seconds() / 60.0
    tiempo_en_brechas_min = brechas_df["duracion_min"].sum() if not brechas_df.empty else 0.0
    tiempo_cubierto_min = tiempo_total_min - tiempo_en_brechas_min
    uptime_pct = 100.0 * tiempo_cubierto_min / tiempo_total_min if tiempo_total_min > 0 else None

    filas_md = "\n".join(
        f"| {h['inicio_local']} | {h['fin_local']} | {h['duracion_min']:.1f} |" for h in huecos
    ) or "| (sin huecos > 3 min) | | |"

    contenido = f"""# B3 — Brechas de datos (huecos > {UMBRAL_MIN:.0f} min)

Horas en America/Mexico_City (UTC-6). Total de huecos detectados: **{len(huecos)}**

| Inicio (local) | Fin (local) | Duración (min) |
|---|---|---|
{filas_md}

- Tiempo total del periodo cubierto por el dataset: {tiempo_total_min:.1f} min ({tiempo_total_min/60:.2f} h)
- Tiempo en brechas: {tiempo_en_brechas_min:.1f} min
- Tiempo cubierto (con lecturas): {tiempo_cubierto_min:.1f} min
- **Uptime % = tiempo cubierto / tiempo total = {uptime_pct:.2f}%**
"""
    SALIDA_MD.write_text(contenido)
    print(f"{len(huecos)} huecos -> {SALIDA_CSV}, {SALIDA_MD}")
    for h in huecos:
        print(h)


if __name__ == "__main__":
    main()
