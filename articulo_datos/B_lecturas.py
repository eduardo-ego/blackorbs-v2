#!/usr/bin/env python3
"""Exporta la tabla lecturas completa (device_id ORBE_001) a B_lecturas.csv.
Solo lectura sobre data/blackorbs.db. Requiere: pandas.
"""
import sqlite3
import pandas as pd
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "data" / "blackorbs.db"
SALIDA = Path(__file__).resolve().parent / "B_lecturas.csv"


def main():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    df = pd.read_sql_query(
        "SELECT timestamp, temperature, humidity FROM lecturas "
        "WHERE device_id = 'ORBE_001' ORDER BY timestamp ASC",
        conn,
    )
    conn.close()
    df.to_csv(SALIDA, index=False)
    print(f"{len(df)} filas -> {SALIDA}")


if __name__ == "__main__":
    main()
