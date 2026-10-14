"""
Detección de anomalías sobre las lecturas del sensor.

Con pocos datos usa un detector estadístico simple (EWMA/z-score) que funciona
desde la primera lectura. Cuando ya hay suficiente historial, cambia a
Isolation Forest (no supervisado, multivariante) reentrenado cada ciclo.
Los umbrales de severidad NO son fijos a mano: se calculan a partir de la
distribución de los propios datos (percentiles / desviaciones estándar).
"""

import numpy as np
from sklearn.ensemble import IsolationForest

from config import VARIABLES, MIN_LECTURAS_MODELO_APRENDIDO

VENTANA_EWMA = 50


def _severidad_desde_z(z_abs):
    if z_abs >= 3.5:
        return "critical"
    if z_abs >= 2.0:
        return "attention"
    return "happy"


def _normalidad_desde_z(z_abs):
    """Convierte un z-score a un % de 'normalidad' fácil de mostrar en la interfaz.
    z=0 -> 100%, z>=4 desviaciones -> 0%. Es una heurística de visualización,
    no cambia la clasificación de severidad (esa sigue siendo _severidad_desde_z)."""
    return round(max(0.0, 100.0 - min(100.0, (z_abs / 4.0) * 100.0)), 1)


def _detectar_ewma(df):
    """Compara la última lectura contra la media/desviación móvil de las anteriores."""
    ventana = df.iloc[-(VENTANA_EWMA + 1):-1] if len(df) > 1 else df.iloc[:0]
    if ventana.empty:
        return {"mood": "happy", "score": 0.0, "variable": None, "normalidad": 100.0,
                "message": "First reading, no reference yet.", "metodo": "ewma"}

    ultima = df.iloc[-1]
    peor_z, peor_var = 0.0, None

    for var in VARIABLES:
        media = ventana[var].mean()
        std = ventana[var].std(ddof=0)
        if std == 0 or np.isnan(std):
            continue
        z = abs((ultima[var] - media) / std)
        if z > peor_z:
            peor_z, peor_var = z, var

    mood = _severidad_desde_z(peor_z)
    mensaje = (
        "No relevant deviations from recent history."
        if mood == "happy"
        else f"{peor_var} deviates {peor_z:.1f} standard deviations from recent readings."
    )
    return {"mood": mood, "score": round(float(peor_z), 3), "variable": peor_var,
            "normalidad": _normalidad_desde_z(peor_z), "message": mensaje, "metodo": "ewma"}


def _detectar_isolation_forest(df):
    datos = df[VARIABLES].dropna()
    if len(datos) < MIN_LECTURAS_MODELO_APRENDIDO:
        return None

    modelo = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
    modelo.fit(datos.values)

    scores = modelo.decision_function(datos.values)  # más bajo = más anómalo
    ultimo_score = scores[-1]

    # % de lecturas históricas con score igual o peor que la actual = qué tan
    # "normal" es esta lectura frente a todo lo visto hasta ahora.
    normalidad = round(float((scores <= ultimo_score).mean() * 100), 1)

    p5, p15 = np.percentile(scores, [5, 15])
    if ultimo_score <= p5:
        mood = "critical"
    elif ultimo_score <= p15:
        mood = "attention"
    else:
        mood = "happy"

    # variable con mayor desviación respecto a su propia media, como pista de causa
    ultima = datos.iloc[-1]
    medias = datos.mean()
    stds = datos.std(ddof=0).replace(0, np.nan)
    z_por_variable = ((ultima - medias) / stds).abs()
    peor_var = z_por_variable.idxmax() if not z_por_variable.isna().all() else None

    mensaje = (
        "Combined temperature/humidity pattern within normal range."
        if mood == "happy"
        else f"Isolation Forest flags this combination of readings as unusual (possible cause: {peor_var})."
    )
    return {"mood": mood, "score": round(float(ultimo_score), 4), "variable": peor_var,
            "normalidad": normalidad, "message": mensaje, "metodo": "isolation_forest"}


def evaluar_valor_futuro(df, variable, valor):
    """Aplica el mismo criterio EWMA a un valor pronosticado (no observado aún),
    para que el forecast pueda anticipar 'attention' antes de que ocurra la anomalía real."""
    if valor is None or df.empty:
        return "happy"

    ventana = df.iloc[-VENTANA_EWMA:]
    std = ventana[variable].std(ddof=0)
    media = ventana[variable].mean()
    if std == 0 or np.isnan(std):
        return "happy"

    z = abs((valor - media) / std)
    return _severidad_desde_z(z)


_ORDEN_SEVERIDAD = {"happy": 0, "attention": 1, "critical": 2}


def peor_mood(*moods):
    return max(moods, key=lambda m: _ORDEN_SEVERIDAD.get(m, 0))


def detectar_anomalia(df):
    if df.empty:
        return {"mood": "happy", "score": None, "variable": None, "normalidad": None,
                "message": "No readings yet.", "metodo": "ninguno"}

    resultado = _detectar_isolation_forest(df)
    if resultado is not None:
        return resultado

    return _detectar_ewma(df)
