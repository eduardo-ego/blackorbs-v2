import sqlite3
import pandas as pd

from config import SQLITE_PATH, VARIABLES


def get_connection():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def cargar_lecturas(device_id, limite=2000):
    conn = get_connection()
    try:
        query = """
            SELECT temperature, humidity, pressure, timestamp
            FROM lecturas
            WHERE device_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(device_id, limite))
    finally:
        conn.close()

    if df.empty:
        return df

    df = df.iloc[::-1].reset_index(drop=True)  # orden cronológico ascendente
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df
