#!/usr/bin/env python3
"""E2 — Banco de 25 preguntas (5 por intención) x 3 repeticiones x proveedor,
enviadas a POST /chat del API real (localhost:3001). Requiere que el servicio
blackorbs-v2-api esté corriendo. Lee APP_PIN de api/.env solo para autenticar
la sesión (nunca se imprime ni se guarda en las salidas).

LIMITACIÓN IMPORTANTE (ver A_herramientas_llm.md): la respuesta de /chat
(`{result, provider}`) NO expone qué tools se invocaron ni sus argumentos —
esa información vive solo en memoria dentro de chatController.js y nunca se
persiste ni se devuelve por HTTP. Por instrucción no se debe modificar el
código para exponerla. Por lo tanto:
  - "tools invocadas y argumentos" y "tool-selection accuracy" quedan como
    "no observable vía API" en la salida (columnas vacías) — requeriría
    instrumentar chatController.js (decisión del autor, no se hizo aquí).
  - La "fidelidad numérica" SÍ se puede evaluar de forma indirecta: el propio
    script consulta la base de datos (solo lectura) para construir el mismo
    conjunto de valores que las tools habrían devuelto en ese momento, y
    compara contra los números que aparecen en la respuesta del LLM.

Salida: E_tabla6_grounding.csv, E_tabla6_grounding.md, E_ejemplos_tabla5.md.
Requiere: requests, pandas.
"""
import json
import os
import re
import sqlite3
import time
from pathlib import Path

import pandas as pd
import requests

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
DB_PATH = RAIZ / "data" / "blackorbs.db"
ENV_PATH = RAIZ / "api" / ".env"

BASE_URL = os.environ.get("BLACKORBS_API_URL", "http://localhost:3001")
DEVICE_ID = "ORBE_001"
REPETICIONES = 3
PROVEEDORES = ["claude"]  # por indicación del usuario: omitir OpenAI por completo

SALIDA_CSV = AQUI / "E_tabla6_grounding.csv"
SALIDA_MD = AQUI / "E_tabla6_grounding.md"
SALIDA_EJEMPLOS = AQUI / "E_ejemplos_tabla5.md"

PREGUNTAS = [
    # (intencion, texto)
    ("estado_actual", "¿Cómo está el ambiente ahorita?"),
    ("estado_actual", "¿Cuál es el estado actual del dispositivo?"),
    ("estado_actual", "¿Hay alguna anomalía en este momento?"),
    ("estado_actual", "Dame la lectura más reciente de temperatura y humedad."),
    ("estado_actual", "¿Qué tan normal es la condición actual según el modelo?"),

    ("estadisticas_periodo", "¿Cuál fue la temperatura promedio en la última hora?"),
    ("estadisticas_periodo", "¿Cuál fue la humedad máxima en los últimos 30 minutos?"),
    ("estadisticas_periodo", "Dame un resumen de las últimas 2 horas de lecturas."),
    ("estadisticas_periodo", "¿Cuánto varió la temperatura en la última hora?"),
    ("estadisticas_periodo", "¿Cuál fue la humedad mínima registrada en los últimos 60 minutos?"),

    ("comparacion_periodos", "¿La temperatura de la última hora es más alta que la de las dos horas anteriores?"),
    ("comparacion_periodos", "Compara la humedad de los últimos 30 minutos contra los 30 minutos previos."),
    ("comparacion_periodos", "¿Ha subido o bajado la temperatura respecto a hace una hora?"),
    ("comparacion_periodos", "¿Está más húmedo ahora que hace 2 horas?"),
    ("comparacion_periodos", "Compara el estado actual contra el forecast pronosticado."),

    ("recuerdo_alertas", "¿Cuáles son las alertas más recientes?"),
    ("recuerdo_alertas", "¿Ha habido alguna anomalía crítica recientemente?"),
    ("recuerdo_alertas", "¿Cuántas alertas de atención se generaron recientemente?"),
    ("recuerdo_alertas", "Dame detalles de la última alerta registrada."),
    ("recuerdo_alertas", "¿Cuál fue la variable responsable de la última anomalía?"),

    ("fuera_de_alcance", "¿Cuál es el pronóstico del clima para mañana en la ciudad?"),
    ("fuera_de_alcance", "¿Cuántos dispositivos Blackorbs existen en el mundo?"),
    ("fuera_de_alcance", "¿Puedes prender el aire acondicionado del cuarto?"),
    ("fuera_de_alcance", "¿Cuál fue la temperatura hace exactamente un año?"),
    ("fuera_de_alcance", "¿Qué opinas de la bolsa de valores hoy?"),
]

NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


def leer_pin():
    for linea in ENV_PATH.read_text().splitlines():
        if linea.startswith("APP_PIN="):
            return linea.split("=", 1)[1].strip()
    raise RuntimeError("APP_PIN no encontrado en api/.env")


def login(sesion):
    pin = leer_pin()
    r = sesion.post(f"{BASE_URL}/login", json={"pin": pin}, timeout=10)
    r.raise_for_status()
    if not r.json().get("ok"):
        raise RuntimeError("Login falló")


def valores_ground_truth():
    """Construye el mismo conjunto de números que las tools reales habrían devuelto
    en este instante, consultando la base de datos en modo solo lectura."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    valores = set()

    estado = pd.read_sql_query("SELECT * FROM ml_estado WHERE device_id = ?", conn, params=(DEVICE_ID,))
    for col in ["anomaly_score", "normalidad_pct", "forecast_temperature", "forecast_humidity",
                "forecast_horizon_minutes"]:
        if not estado.empty and pd.notna(estado.iloc[0].get(col)):
            valores.add(round(float(estado.iloc[0][col]), 1))
            valores.add(round(float(estado.iloc[0][col])))

    ultima = pd.read_sql_query(
        "SELECT * FROM lecturas WHERE device_id=? ORDER BY timestamp DESC LIMIT 1", conn, params=(DEVICE_ID,))
    for col in ["temperature", "humidity"]:
        if not ultima.empty:
            valores.add(round(float(ultima.iloc[0][col]), 1))
            valores.add(round(float(ultima.iloc[0][col])))

    for minutos in [30, 60, 120]:
        hist = pd.read_sql_query(
            f"SELECT temperature, humidity FROM lecturas WHERE device_id=? "
            f"AND timestamp >= datetime('now', '-{minutos} minutes')", conn, params=(DEVICE_ID,))
        for col in ["temperature", "humidity"]:
            if not hist.empty:
                for stat in [hist[col].mean(), hist[col].min(), hist[col].max()]:
                    valores.add(round(float(stat), 1))
                    valores.add(round(float(stat)))

    alertas = pd.read_sql_query("SELECT * FROM alertas ORDER BY timestamp DESC LIMIT 10", conn)
    valores.add(len(alertas))
    for _, a in alertas.iterrows():
        if pd.notna(a.get("value")):
            valores.add(round(float(a["value"]), 1))
            valores.add(round(float(a["value"])))

    conn.close()
    return valores


def extraer_numeros(texto):
    nums = []
    for m in NUM_RE.findall(texto or ""):
        try:
            nums.append(float(m.replace(",", ".")))
        except ValueError:
            pass
    return nums


def coincide(n, ground_truth, tol_abs=0.6):
    return any(abs(n - g) <= tol_abs for g in ground_truth)


def enviar_pregunta(sesion, pregunta, proveedor):
    t0 = time.perf_counter()
    try:
        r = sesion.post(f"{BASE_URL}/chat", json={"message": pregunta, "provider": proveedor}, timeout=60)
        latencia = time.perf_counter() - t0
        if r.status_code != 200:
            return {"ok": False, "status": r.status_code, "error": r.json().get("error"), "latencia_s": latencia}
        return {"ok": True, "respuesta": r.json().get("result"), "latencia_s": latencia}
    except requests.RequestException as e:
        return {"ok": False, "status": None, "error": str(e), "latencia_s": time.perf_counter() - t0}


def main():
    sesion = requests.Session()
    login(sesion)

    gt = valores_ground_truth()
    filas = []
    ejemplos = {}
    openai_deshabilitado = False

    for intencion, pregunta in PREGUNTAS:
        for proveedor in PROVEEDORES:
            if proveedor == "openai" and openai_deshabilitado:
                filas.append({"intencion": intencion, "pregunta": pregunta, "proveedor": proveedor,
                              "intento": None, "ok": False, "error": "omitido: sin créditos (detectado antes)",
                              "latencia_s": None, "n_numeros": None, "n_respaldados": None,
                              "declara_sin_datos": None})
                continue
            for intento in range(1, REPETICIONES + 1):
                res = enviar_pregunta(sesion, pregunta, proveedor)
                if not res["ok"]:
                    if proveedor == "openai" and "créditos" in (res.get("error") or "").lower():
                        openai_deshabilitado = True
                    filas.append({"intencion": intencion, "pregunta": pregunta, "proveedor": proveedor,
                                  "intento": intento, "ok": False, "error": res.get("error"),
                                  "latencia_s": res["latencia_s"], "n_numeros": None,
                                  "n_respaldados": None, "declara_sin_datos": None})
                    continue

                texto = res["respuesta"] or ""
                numeros = extraer_numeros(texto)
                respaldados = sum(1 for n in numeros if coincide(n, gt))
                declara_sin_datos = intencion == "fuera_de_alcance" and any(
                    p in texto.lower() for p in ["no tengo", "no puedo", "fuera de mi alcance",
                                                  "no cuento con", "no dispongo", "no es algo que pueda"])

                filas.append({"intencion": intencion, "pregunta": pregunta, "proveedor": proveedor,
                              "intento": intento, "ok": True, "error": None,
                              "latencia_s": res["latencia_s"], "n_numeros": len(numeros),
                              "n_respaldados": respaldados, "declara_sin_datos": declara_sin_datos})

                if intencion not in ejemplos:
                    ejemplos[intencion] = {"pregunta": pregunta, "proveedor": proveedor, "respuesta": texto,
                                            "latencia_s": res["latencia_s"]}

    detalle = pd.DataFrame(filas)
    detalle.to_csv(SALIDA_CSV, index=False)

    resumen = (
        detalle[detalle["ok"]]
        .groupby(["proveedor", "intencion"])
        .agg(n=("ok", "count"), latencia_media_s=("latencia_s", "mean"),
             numeros_totales=("n_numeros", "sum"), numeros_respaldados=("n_respaldados", "sum"))
        .reset_index()
    )
    resumen["fidelidad_numerica_pct"] = (
        100 * resumen["numeros_respaldados"] / resumen["numeros_totales"].replace(0, pd.NA)
    )

    md = ["# E2 — Tabla 6: grounding / fidelidad numérica del chat LLM", "",
          "**Nota de metodología:** tool-selection accuracy y 'tools invocadas y argumentos' "
          "no son observables desde /chat (ver cabecera de E_benchmark_chat.py) — no se "
          "reportan aquí. La fidelidad numérica se calculó comparando los números en la "
          "respuesta contra un ground-truth calculado por el propio script vía consultas SQL "
          "directas (tolerancia ±0.6) al momento de cada pregunta.",
          "",
          "| Proveedor | Intención | N respuestas OK | Latencia media (s) | Números totales | Respaldados | Fidelidad % |",
          "|---|---|---|---|---|---|---|"]
    for _, r in resumen.iterrows():
        fid = f"{r['fidelidad_numerica_pct']:.1f}" if pd.notna(r['fidelidad_numerica_pct']) else "s/d"
        md.append(f"| {r['proveedor']} | {r['intencion']} | {int(r['n'])} | "
                   f"{r['latencia_media_s']:.2f} | {int(r['numeros_totales'])} | "
                   f"{int(r['numeros_respaldados'])} | {fid} |")

    fallos = detalle[~detalle["ok"]]
    if not fallos.empty:
        md.append("")
        md.append(f"Llamadas fallidas/omitidas: {len(fallos)} (ver columna `error` en "
                   f"`E_tabla6_grounding.csv`).")

    SALIDA_MD.write_text("\n".join(md) + "\n")

    ej_md = ["# E_ejemplos_tabla5 — Una interacción real por intención", ""]
    for intencion, info in ejemplos.items():
        ej_md += [f"## {intencion}", "", f"**Pregunta:** {info['pregunta']}",
                  f"**Proveedor:** {info['proveedor']}  ",
                  f"**Latencia:** {info['latencia_s']:.2f} s", "", "**Respuesta:**", "```",
                  info["respuesta"], "```", ""]
    SALIDA_EJEMPLOS.write_text("\n".join(ej_md) + "\n")

    print(f"-> {SALIDA_CSV}\n-> {SALIDA_MD}\n-> {SALIDA_EJEMPLOS}")
    print(f"{len(detalle)} llamadas registradas, {(~detalle['ok']).sum()} fallidas/omitidas.")


if __name__ == "__main__":
    main()
