#!/usr/bin/env python3
"""F4 — Escucha nuevas filas en `alertas` (solo lectura, polling) y te pide confirmar
manualmente a qué hora llegó la notificación por cada canal (Telegram/WhatsApp/email),
para calcular la latencia end-to-end real. Se detiene tras registrar N_EVENTOS (default 20)
o con Ctrl+C (lo ya registrado se guarda igual).

No envía nada ni modifica la base de datos — es un cronómetro que corre en paralelo a las
alertas reales que ya genera el sistema (ver alertNotifier.js).

Salida: F_latencia_alertas_muestras.csv.
Requiere: pandas.
"""
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "data" / "blackorbs.db"
SALIDA = Path(__file__).resolve().parent / "F_latencia_alertas_muestras.csv"
N_EVENTOS = 20
POLL_S = 5


def ultima_id_alerta(conn):
    row = conn.execute("SELECT MAX(id) FROM alertas").fetchone()
    return row[0] or 0


def main():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    ultimo_id = ultima_id_alerta(conn)
    print(f"Escuchando alertas nuevas (id > {ultimo_id}). Ctrl+C para detener.")

    registros = []
    try:
        while len(registros) < N_EVENTOS:
            time.sleep(POLL_S)
            df = pd.read_sql_query("SELECT * FROM alertas WHERE id > ? ORDER BY id ASC",
                                    conn, params=(ultimo_id,))
            if df.empty:
                continue
            for _, alerta in df.iterrows():
                ultimo_id = max(ultimo_id, alerta["id"])
                ts_alerta = pd.Timestamp(alerta["timestamp"], tz="UTC")
                print(f"\nNueva alerta #{alerta['id']} a las {ts_alerta.isoformat()} "
                      f"({alerta['severity']}): {alerta['message']}")
                llegada = {}
                for canal in ["telegram", "whatsapp", "email"]:
                    resp = input(f"  Hora de llegada por {canal} (HH:MM:SS local, o vacío si no aplica/no llegó): ").strip()
                    llegada[canal] = resp or None
                registros.append({"alerta_id": alerta["id"], "timestamp_alerta_utc": ts_alerta.isoformat(),
                                   **{f"llegada_{c}": v for c, v in llegada.items()}})
    except KeyboardInterrupt:
        print("\nInterrumpido, guardando lo registrado hasta ahora...")
    finally:
        conn.close()

    if registros:
        pd.DataFrame(registros).to_csv(SALIDA, index=False)
        print(f"-> {SALIDA} ({len(registros)} eventos)")
        print("Calcula la latencia restando timestamp_alerta_utc (UTC) de cada hora de "
              "llegada (conviértela a UTC primero, America/Mexico_City = UTC-6).")
    else:
        print("No se registró ningún evento.")


if __name__ == "__main__":
    main()
