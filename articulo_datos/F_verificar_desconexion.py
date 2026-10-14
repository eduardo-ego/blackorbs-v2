#!/usr/bin/env python3
"""F1 — Verifica, después de una prueba de desconexión de uplink hecha manualmente,
que no faltaron lecturas, que ml_estado siguió actualizándose, y cuántas alertas se
generaron en la ventana. Solo lectura sobre data/blackorbs.db.

Uso:
    python F_verificar_desconexion.py --inicio 2026-09-10T10:00:00 --fin 2026-09-10T12:30:00

Las horas se interpretan en America/Mexico_City si no traen zona horaria.
Requiere: pandas.
"""
import argparse
import sqlite3
from pathlib import Path

import pandas as pd
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "data" / "blackorbs.db"
TZ = ZoneInfo("America/Mexico_City")
DEVICE_ID = "ORBE_001"
INTERVALO_ESPERADO_S = 60


def parse_ts(s):
    t = pd.Timestamp(s)
    return t.tz_localize(TZ) if t.tz is None else t.tz_convert(TZ)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    args = ap.parse_args()

    ini, fin = parse_ts(args.inicio), parse_ts(args.fin)

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

    lecturas = pd.read_sql_query(
        "SELECT timestamp, temperature, humidity FROM lecturas WHERE device_id = ? "
        "AND timestamp BETWEEN ? AND ? ORDER BY timestamp ASC",
        conn, params=(DEVICE_ID, ini.tz_convert("UTC").isoformat(), fin.tz_convert("UTC").isoformat()),
    )
    lecturas["timestamp"] = pd.to_datetime(lecturas["timestamp"], utc=True)

    estado_historico = pd.read_sql_query(
        "SELECT updated_at FROM ml_estado WHERE device_id = ?", conn, params=(DEVICE_ID,))

    alertas = pd.read_sql_query(
        "SELECT * FROM alertas WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp ASC",
        conn, params=(ini.tz_convert("UTC").isoformat(), fin.tz_convert("UTC").isoformat()))

    conn.close()

    print(f"Ventana evaluada: {ini.isoformat()} -> {fin.isoformat()} "
          f"({(fin-ini).total_seconds()/3600:.2f} h)")
    print(f"Lecturas encontradas en la ventana: {len(lecturas)}")

    if len(lecturas) >= 2:
        diffs_s = lecturas["timestamp"].diff().dt.total_seconds().dropna()
        huecos = diffs_s[diffs_s > 180]
        print(f"Huecos > 3 min dentro de la ventana: {len(huecos)}")
        if len(huecos):
            print(huecos)
        cobertura_pct = 100 * (1 - huecos.sum() / (fin - ini).total_seconds())
        print(f"Cobertura de datos en la ventana: {cobertura_pct:.2f}%")
    else:
        print("Muy pocas lecturas para evaluar huecos (revisa si el rango es correcto).")

    print(f"\nml_estado.updated_at más reciente en TODO el historial: "
          f"{estado_historico['updated_at'].iloc[0] if not estado_historico.empty else 'N/D'}")
    print("(Compara manualmente contra el fin de la ventana para confirmar que ml_estado "
          "se siguió actualizando durante el corte; ml_estado no guarda historial, solo el "
          "estado más reciente por device_id.)")

    print(f"\nAlertas generadas en la ventana: {len(alertas)}")
    if not alertas.empty:
        print(alertas[["timestamp", "type", "severity", "message"]].to_string(index=False))
        print("\nRevisa manualmente si estas alertas llegaron por Telegram/Teams durante el "
              "corte (ver F_desconexion.md: no hay reintentos automáticos si el envío falla "
              "por falta de uplink — solo quedan registradas en esta tabla).")


if __name__ == "__main__":
    main()
