import sqlite3

from config import SQLITE_PATH, DEVICE_ID


def get_connection():
    conn = sqlite3.connect(SQLITE_PATH, timeout=2)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def ultima_lectura():
    try:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT temperature, humidity, timestamp FROM lecturas "
                "WHERE device_id = ? ORDER BY timestamp DESC LIMIT 1",
                (DEVICE_ID,),
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return None
    if not row:
        return None
    return {"temperature": row[0], "humidity": row[1], "timestamp": row[2]}


def estado_ml():
    try:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT mood FROM ml_estado WHERE device_id = ?", (DEVICE_ID,)
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return "happy"
    if not row or not row[0]:
        return "happy"
    return row[0]
