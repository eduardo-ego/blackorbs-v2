# A1 — Parámetros del pipeline de ML (leído de ml/config.py, ml/anomaly.py, ml/forecast.py, ml/service.py)

> Nota importante: el código real **no implementa un EWMA con λ (alpha) clásico** (media/varianza
> con actualización recursiva `x_t = λ·v_t + (1-λ)·x_{t-1}`). Lo que hay es una **ventana móvil
> simple** de tamaño fijo `VENTANA_EWMA = 50` (últimas 50 lecturas antes de la actual, excluyendo la
> lectura evaluada) sobre la que se calcula media y desviación estándar poblacional
> (`std(ddof=0)`), y luego un z-score de la lectura más reciente contra esa media/std. El nombre de
> la función es `_detectar_ewma` mero por convención de nombre en el código; no hay ningún parámetro
> `alpha`/`λ` en config.py ni en anomaly.py. Si el artículo necesita citar un "λ del EWMA", **no
> existe tal valor en el sistema real** — hay que corregir la sección 4.2/4.4 del artículo para
> describir esto como "detector estadístico de ventana móvil (n=50)" en vez de EWMA con λ.

- **Ventana del detector estadístico (etapa 1):** `VENTANA_EWMA = 50` lecturas (constante en
  `ml/anomaly.py`, no configurable por variable de entorno).
- **Cálculo:** para cada variable en `VARIABLES = ["temperature", "humidity"]`, `media` y `std`
  (poblacional, ddof=0) de las 50 lecturas previas a la actual; `z = |valor_actual - media| / std`.
  Se toma la variable con mayor `z` ("peor_z", "peor_var").
- **Umbrales de severidad (etapa 1)**, función `_severidad_desde_z`:
  - `z >= 3.5` → `critico`
  - `2.0 <= z < 3.5` → `atencion`
  - `z < 2.0` → `contento`
- **`normalidad_pct` en etapa 1** (`_normalidad_desde_z`): heurística de visualización, no afecta la
  severidad. `normalidad = max(0, 100 - min(100, (z/4.0)*100))`, redondeado a 1 decimal (z=0 → 100%;
  z>=4 → 0%).

## Transición a Isolation Forest (etapa 2)

- **`MIN_LECTURAS_MODELO_APRENDIDO = 200`** (constante en `ml/config.py`, no viene de variable de
  entorno pese a que otras sí). Coincide con lo esperado en las instrucciones.
- **Criterio de transición:** en `detectar_anomalia(df)`, primero se intenta
  `_detectar_isolation_forest(df)`; esa función devuelve `None` si
  `len(datos.dropna()) < MIN_LECTURAS_MODELO_APRENDIDO`, y solo entonces se usa
  `_detectar_ewma(df)` como *fallback*. Es decir: **Isolation Forest tiene prioridad siempre que haya
  ≥200 lecturas válidas (sin NaN) de temperatura+humedad**; con menos, se usa el detector de ventana
  móvil de la etapa 1. No hay un modo mixto ni un periodo de transición gradual.
- **Datos de entrenamiento:** no hay una "ventana de entrenamiento" separada — se usa **todo el
  historial cargado**, y ese historial ya viene acotado por `ml/db.py::cargar_lecturas(device_id,
  limite=2000)`: las **últimas 2000 lecturas** del dispositivo (a ~60 s/lectura ≈ 33.3 h de
  historial máximo). Si hay ≥200 y ≤2000 lecturas, se entrena con todas las disponibles.

### Isolation Forest — hiperparámetros exactos (`ml/anomaly.py::_detectar_isolation_forest`)

| Parámetro | Valor |
|---|---|
| `n_estimators` | 200 |
| `contamination` | `"auto"` (no es un número fijo) |
| `max_samples` | no se especifica → default de scikit-learn, `"auto"` (= `min(256, n_samples)`) |
| `random_state` | 42 |
| Ventana de entrenamiento | todo el df cargado (hasta 2000 lecturas, ver arriba) |
| Frecuencia de reentrenamiento | **cada ciclo** (se llama `modelo.fit()` de nuevo en cada ejecución de `ejecutar_ciclo()`, cada `CICLO_SEGUNDOS` = 60 s) — no hay caché de modelo entre ciclos |

### Percentiles etapa 2 y `normalidad_pct`

- `ultimo_score = modelo.decision_function(datos.values)[-1]` (más bajo = más anómalo).
- `p5, p15 = np.percentile(scores, [5, 15])` sobre **todos** los scores del historial cargado
  (incluye el de la lectura actual).
- Regla: `score <= p5` → `critico`; `p5 < score <= p15` → `atencion`; si no, `contento`.
  (Nota: las instrucciones mencionaban "percentiles para atención/crítico"; el real usa **p5 para
  crítico y p15 para atención**, no p50 ni otros valores.)
- `normalidad_pct = round(mean(scores <= ultimo_score) * 100, 1)` — porcentaje de lecturas
  históricas con score igual o peor (más anómalo) que la actual.
- Variable señalada como causa (`variable`): la de mayor `|z|` respecto a su propia media/std
  dentro del mismo conjunto de datos usado por Isolation Forest (no viene del modelo en sí, es una
  pista adicional calculada aparte).

## Forecast (`ml/forecast.py`)

- **`MIN_PUNTOS_HOLT = 30`** — umbral de puntos para pasar de persistencia a Holt. Coincide
  exactamente con lo esperado (~30) en las instrucciones.
- **Regla real usada en `generar_forecast`:** no se compara directo contra `MIN_PUNTOS_HOLT`, sino
  contra `minimo_puntos = max(MIN_PUNTOS_HOLT, pasos * 2)`, donde `pasos` es el horizonte en pasos
  (ver abajo). Es decir, para horizontes largos el umbral efectivo de puntos requeridos puede ser
  mayor a 30.
- **Horizonte de pronóstico:**
  - `HORIZONTE_MINUTOS = 60` (env `ML_HORIZONTE_MINUTOS`, default 60 minutos).
  - `intervalo` = mediana de las diferencias entre timestamps del propio df (en minutos), con piso
    de 10.0 si no hay suficientes datos o la mediana es 0/None.
  - `pasos = max(1, round(HORIZONTE_MINUTOS / intervalo))`.
  - `horizonte_minutos` reportado = `round(intervalo * pasos)` (puede diferir levemente de 60 si el
    intervalo real no divide exacto).
  - Con el intervalo real del sensor (~60 s = 1 min), `pasos ≈ 60` y `horizonte_minutos ≈ 60`.
- **`ExponentialSmoothing` (statsmodels), por variable:**
  - `trend = "add"`
  - `damped_trend = True`
  - `seasonal`: **no se especifica** → sin componente estacional (default `None`)
  - `initialization_method = "estimated"`
  - Se entrena por separado para `temperature` y `humidity`.
- **Regla exacta que activa `confianza_baja`:**
  `confianza_baja = temp_baja OR hum_baja`, y cada `*_baja` es `True` si:
  - la serie de esa variable (sin NaN) tiene `len(serie) < minimo_puntos` (persistencia, no se
    llega a entrenar Holt), **o**
  - `ExponentialSmoothing(...).fit()` o `.forecast()` lanza una excepción (fallback a persistencia).
  - Si `df` está vacío, `confianza_baja = True` para ambas variables.

## Intervalos de ciclo del sistema

| Constante | Valor | Origen |
|---|---|---|
| `CICLO_SEGUNDOS` (ML) | 60 s | `ml/config.py`, env `ML_CICLO_SEGUNDOS` |
| `SENSOR_INTERVALO_SEGUNDOS` | 60 s | `sensor/config.py`, env `SENSOR_INTERVALO_SEGUNDOS` |
| `DISPLAY_REFRESCO_SEGUNDOS` | 60 s | `display/config.py`, env `DISPLAY_REFRESCO_SEGUNDOS` |

Los tres están igualados a 60 s por diseño (ver comentario en `display/config.py`: el display se
igualó al intervalo del sensor a propósito, tras medir que animar continuamente calentaba el sensor
~1–2 °C por carga sostenida de CPU — ver sección C).

## Regla de agregación de `mood` (`ml/service.py::ejecutar_ciclo`)

1. `anomalia = detectar_anomalia(df)` → mood de la etapa 1 o 2 (contento/atencion/critico).
2. Si `forecast["confianza_baja"]` es `False` (confianza alta):
   - se evalúa el valor pronosticado de temperatura y de humedad, cada uno contra el mismo criterio
     de z-score de la etapa 1 (`evaluar_valor_futuro`, usa las últimas `VENTANA_EWMA=50` lecturas
     reales como referencia, **no** reentrenando Isolation Forest sobre el valor futuro).
   - `mood_forecast = peor_mood(mood_forecast_temp, mood_forecast_hum)`.
   - Si `confianza_baja` es `True`, `mood_forecast = "contento"` siempre (no se penaliza por un
     forecast en el que no se confía).
3. `mood_final = peor_mood(anomalia["mood"], mood_forecast)`, con orden de severidad
   `contento(0) < atencion(1) < critico(2)` (`peor_mood` = el de mayor severidad de los que se le
   pasen).
4. El mensaje mostrado es el de `anomalia["message"]`, salvo que la anomalía sea "contento" y el
   forecast no lo sea — en ese caso se sobreescribe con: *"El forecast anticipa que las condiciones
   podrían salirse de rango pronto."*

## Otras notas relevantes para el artículo

- El servicio ML solo recalcula/escribe estado; el LLM del chat **nunca** calcula anomalías o
  forecast — solo lee `ml_estado` vía herramientas (ver `A_herramientas_llm.md`).
- El hardware real es un **SHT85** (I2C 0x44), no un BME680; por eso `VARIABLES` no incluye
  `pressure` aunque la columna exista en el esquema (ver `sensor/read_loop.py`, comentario explícito
  sobre el cambio respecto a v1).
