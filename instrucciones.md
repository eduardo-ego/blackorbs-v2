Datos pendientes para el artículo v17 — extracción desde el dispositivo

Contexto para Claude Code: el sistema v2 vive en /home/blackorbs/blackorbs-v2/ (api/, ml/, sensor/, display/, data/blackorbs.db). Necesito que extraigas la siguiente información y la entregues en archivos separados dentro de una carpeta articulo_datos/. No modifiques el código ni la base de datos; solo lee. Para todo lo que sea cálculo, deja también el script que lo generó.

A. Configuración y parámetros del modelo (leer del código)

A1. De ml/config.py, ml/anomaly.py, ml/forecast.py y ml/service.py extraer y documentar en A_parametros_ml.md:

λ (alpha) del EWMA y cómo se calcula la varianza exponencial.
Umbrales de severidad en etapa 1 (múltiplos de σ para atención y crítico).
MIN_LECTURAS_MODELO_APRENDIDO (esperado 200) y criterio de transición a Isolation Forest.
Isolation Forest: n_estimators, contamination, max_samples, tamaño de la ventana de entrenamiento, frecuencia de reentrenamiento, random_state.
Percentiles usados para atención / crítico en etapa 2 y cómo se calcula normalidad_pct.
Forecast: umbral de puntos para pasar de persistencia a Holt (esperado ~30), horizonte de pronóstico (pasos y minutos), parámetros de ExponentialSmoothing (damped, trend, seasonal), y la regla exacta que activa confianza_baja.
CICLO_SEGUNDOS, SENSOR_INTERVALO_SEGUNDOS, DISPLAY_REFRESCO_SEGUNDOS.
Regla de agregación de mood (cómo se combinan las severidades de temperatura y humedad).

A2. De api/controllers/chatController.js extraer a A_herramientas_llm.md: nombre, descripción y parámetros exactos de cada tool (function calling), el system prompt, los modelos usados por proveedor (claude-opus-5, modelo de OpenAI), max_tokens, y el límite de iteraciones del loop de tool-use.

A3. De api/db/schema.sql: esquema completo de las 4 tablas → A_schema.sql.

A4. Licencia del repositorio y URL pública definitiva del proyecto (confirmar si github.com/eduardo-ego/aiot_ciateq es la correcta y qué licencia tiene).

B. Dataset y operación (consultas a data/blackorbs.db, tabla lecturas)

B1. Exportar lecturas completa a B_lecturas.csv (timestamp, temperature, humidity).

B2. Generar B_resumen_dataset.md con: fecha/hora de la primera y última lectura, número total de lecturas, días de operación, intervalo de muestreo efectivo (mediana de las diferencias entre timestamps), y para temperatura y humedad: media, desviación estándar, mínimo, máximo, percentiles 5/50/95.

B3. Detección de brechas: listar todos los huecos > 3 minutos (inicio, fin, duración). Debe aparecer el del 2026-08-24 05:26–20:51 y los del 2026-08-23 (124 min y 13 min). Calcular uptime % = tiempo cubierto / tiempo total. Guardar en B_brechas.csv.

B4. Gráfica de temperatura y humedad de todo el periodo (dos paneles, eje X con fechas, marcar las brechas en gris) → B_fig8_serie_completa.png a 300 dpi, tamaño 6.5 × 3.5 in.

B5. Descripción de las instalaciones: no está en el código; el usuario debe indicar sector, tipo de sala, setpoints nominales de T/HR y fechas de despliegue. Dejar una plantilla en B_instalaciones.md para que la llene.

C. Experimento de autocalentamiento (sección 4.3)

C1. Con journalctl -u blackorbs-v2-display --no-pager -o short-iso, obtener las marcas de tiempo exactas de todos los start/stop del servicio de display (especialmente el día de la prueba on/off/on y la re-prueba post-corrección).

C2. Exportar lecturas en una ventana de −60 min a +60 min alrededor de cada transición → C_selfheating_series.csv.

C3. Calcular por ventana: media, desviación estándar, número de muestras y pendiente (°C/min) en: línea base (display off), animación continua (15 min), tras detener (10 min), y duty-cycled (15 min). Guardar en C_selfheating_tabla.md.

C4. Gráfica de la serie de 60 s con las transiciones marcadas con líneas verticales → C_fig9_selfheating_serie.png (300 dpi, 3.2 × 2.4 in).

C5. Si existe git log del cambio a duty-cycle en display/ring_display.py, anotar el commit y la fecha.

D. Evaluación del detector de anomalías y del pronóstico (sección 4.4, Tablas 3 y 4)

D1. Escribir D_eval_anomalias.py que, sobre B_lecturas.csv, ejecute offline:

Baselines: umbral fijo (usar los umbrales configurados en alertas o, si no hay, ±2σ del dataset completo) y z-score rodante (ventana 60 muestras).
Etapa 1 (EWMA z-score) y etapa 2 (Isolation Forest) importando el código real de ml/anomaly.py, no reimplementándolo.
Conjunto de prueba: segmentos de comportamiento normal (sin alertas ni brechas) en los que se inyectan anomalías sintéticas de tres familias: escalones (±2, ±4, ±8 °C; ±5, ±10, ±20 %HR), rampas (0.05–0.5 °C/min durante 10–60 min) y picos de 1–3 muestras. Mínimo 30 inyecciones por familia, semilla fija.
Reportar por detector y por familia: precisión, recall, F1, retardo medio de detección (muestras) y tiempo de CPU por ciclo en la CM5 (medir con time.perf_counter).
Además, métricas de la etapa 2 en función del número de muestras de entrenamiento (100, 200, 500, 1000) para justificar el hand-over en 200.
Salida: D_tabla3_anomalias.csv y D_tabla3_anomalias.md.

D2. Escribir D_eval_forecast.py: evaluación rolling-origin sobre B_lecturas.csv con el horizonte real del sistema, comparando persistencia vs. Holt damped (importando ml/forecast.py). Reportar MAE y RMSE por variable, y separados por confianza_baja = verdadero/falso. Salida: D_tabla4_forecast.csv y .md.

D3. Registrar el pico sintético de 45 °C que ya se probó: buscar en ml_estado / logs (journalctl -u blackorbs-v2-ml) la marca de tiempo y el resultado (critico) → D_pico_sintetico.md.

D4. Medir consumo de recursos del servicio ML en la CM5: CPU % y RAM del proceso durante 10 ciclos (ps/psutil), y tiempo de entrenamiento del Isolation Forest → D_recursos_ml.md.

E. Evaluación de la interfaz de lenguaje natural (sección 4.5, Tablas 5 y 6)

E1. Exportar la tabla consultas_ia completa a E_consultas_ia.csv (pregunta, proveedor, modelo, tools invocadas, resultados de tools, respuesta, latencia si está guardada, timestamp).

E2. Escribir E_benchmark_chat.py que envíe a POST /chat un banco de 25 preguntas (5 por intención: estado actual; estadísticas de un periodo; comparación entre periodos; recuerdo de alertas/anomalías; fuera de alcance o sin datos), cada una 3 veces por proveedor (OpenAI y Claude; si OpenAI sigue sin créditos, registrarlo y correr solo Claude). Para cada respuesta registrar:

tools invocadas y argumentos;
si son las esperadas (tool-selection accuracy);
todos los números que aparecen en la respuesta y si cada uno coincide (±redondeo) con algún valor devuelto por las tools (fidelidad numérica; cualquier número sin respaldo = alucinación);
en los casos sin datos, si la respuesta declara explícitamente la ausencia;
latencia end-to-end (envío → respuesta completa) y número de tool calls.
Salida: E_tabla6_grounding.csv/.md y E_ejemplos_tabla5.md con 4 interacciones reales (una por intención) para la Tabla 5.
F. Tolerancia a fallos, alertas y potencia (sección 4.6)

F1. Prueba de desconexión: documentar el procedimiento para desconectar el uplink (Tailscale/WiFi) durante ≥ 2 h y, después, verificar con SQL que no faltan lecturas, que ml_estado siguió actualizándose y que se generaron alertas si aplicó. Indicar si las notificaciones generadas durante el corte se reintentan o solo quedan registradas. Salida: F_desconexion.md. (Si el usuario prefiere, dejar solo el script F_verificar_desconexion.py y que él ejecute la desconexión física.)

F2. Fuga de file descriptors: recuperar del journalctl -u blackorbs-v2-sensor la primera aparición de Errno 24 y confirmar el commit del with SMBus(...). Si existe un watchdog/heartbeat (alerta cuando la última lectura es más antigua que k intervalos), describirlo; si no existe, indicarlo → F_fd_leak.md.

F3. Reinicio por Piper: extraer del journal las líneas -- Boot -- y la actividad /tts de ~21 s antes, con timestamps → F_piper_reboot.md.

F4. Latencia de alertas: verificar estado de credenciales de Twilio/Telegram/email (probar un envío). Si funcionan, medir sobre ≥ 20 eventos el tiempo desde el timestamp de la lectura hasta la entrega por canal → F_latencia_alertas.md.

F5. Potencia con el servicio ML activo: no es medible desde software; dejar instrucciones para medir con un medidor USB/DC durante 1 h con todos los servicios corriendo → plantilla en F_potencia.md.

G. Verificaciones bibliográficas (no van en el dispositivo; para el autor)

G1. Confirmar las celdas "Partial" de la Tabla 1 contra los artículos citados (Hassan 2020, Medagedara 2024, Roostaei 2023, Halenár 2025, Dera 2026, Hidalgo-Castelo 2026).

G2. Confirmar la fuente real de la cita "priorización de eventos (Zhang et al., 2021)" del v16; en la lista solo existe Zhang y Tao (2021).

G3. Evidencia socio-técnica de planta (sección 5.1): número de alertas atendidas, tiempo de reacción antes/después, comentarios del personal.

Entrega

Comprimir articulo_datos/ (CSV, MD, PNG y scripts) y pasármela; con eso completo las Tablas 3, 4, 5, 6 y 7, regenero las Figuras 8 y 9, y sustituyo todos los marcadores amarillos del artículo.Datos pendientes para el artículo v17 — extracción desde el dispositivo

Contexto para Claude Code: el sistema v2 vive en /home/blackorbs/blackorbs-v2/ (api/, ml/, sensor/, display/, data/blackorbs.db). Necesito que extraigas la siguiente información y la entregues en archivos separados dentro de una carpeta articulo_datos/. No modifiques el código ni la base de datos; solo lee. Para todo lo que sea cálculo, deja también el script que lo generó.

A. Configuración y parámetros del modelo (leer del código)

A1. De ml/config.py, ml/anomaly.py, ml/forecast.py y ml/service.py extraer y documentar en A_parametros_ml.md:

λ (alpha) del EWMA y cómo se calcula la varianza exponencial.
Umbrales de severidad en etapa 1 (múltiplos de σ para atención y crítico).
MIN_LECTURAS_MODELO_APRENDIDO (esperado 200) y criterio de transición a Isolation Forest.
Isolation Forest: n_estimators, contamination, max_samples, tamaño de la ventana de entrenamiento, frecuencia de reentrenamiento, random_state.
Percentiles usados para atención / crítico en etapa 2 y cómo se calcula normalidad_pct.
Forecast: umbral de puntos para pasar de persistencia a Holt (esperado ~30), horizonte de pronóstico (pasos y minutos), parámetros de ExponentialSmoothing (damped, trend, seasonal), y la regla exacta que activa confianza_baja.
CICLO_SEGUNDOS, SENSOR_INTERVALO_SEGUNDOS, DISPLAY_REFRESCO_SEGUNDOS.
Regla de agregación de mood (cómo se combinan las severidades de temperatura y humedad).

A2. De api/controllers/chatController.js extraer a A_herramientas_llm.md: nombre, descripción y parámetros exactos de cada tool (function calling), el system prompt, los modelos usados por proveedor (claude-opus-5, modelo de OpenAI), max_tokens, y el límite de iteraciones del loop de tool-use.

A3. De api/db/schema.sql: esquema completo de las 4 tablas → A_schema.sql.

A4. Licencia del repositorio y URL pública definitiva del proyecto (confirmar si github.com/eduardo-ego/aiot_ciateq es la correcta y qué licencia tiene).

B. Dataset y operación (consultas a data/blackorbs.db, tabla lecturas)

B1. Exportar lecturas completa a B_lecturas.csv (timestamp, temperature, humidity).

B2. Generar B_resumen_dataset.md con: fecha/hora de la primera y última lectura, número total de lecturas, días de operación, intervalo de muestreo efectivo (mediana de las diferencias entre timestamps), y para temperatura y humedad: media, desviación estándar, mínimo, máximo, percentiles 5/50/95.

B3. Detección de brechas: listar todos los huecos > 3 minutos (inicio, fin, duración). Debe aparecer el del 2026-08-24 05:26–20:51 y los del 2026-08-23 (124 min y 13 min). Calcular uptime % = tiempo cubierto / tiempo total. Guardar en B_brechas.csv.

B4. Gráfica de temperatura y humedad de todo el periodo (dos paneles, eje X con fechas, marcar las brechas en gris) → B_fig8_serie_completa.png a 300 dpi, tamaño 6.5 × 3.5 in.

B5. Descripción de las instalaciones: no está en el código; el usuario debe indicar sector, tipo de sala, setpoints nominales de T/HR y fechas de despliegue. Dejar una plantilla en B_instalaciones.md para que la llene.

C. Experimento de autocalentamiento (sección 4.3)

C1. Con journalctl -u blackorbs-v2-display --no-pager -o short-iso, obtener las marcas de tiempo exactas de todos los start/stop del servicio de display (especialmente el día de la prueba on/off/on y la re-prueba post-corrección).

C2. Exportar lecturas en una ventana de −60 min a +60 min alrededor de cada transición → C_selfheating_series.csv.

C3. Calcular por ventana: media, desviación estándar, número de muestras y pendiente (°C/min) en: línea base (display off), animación continua (15 min), tras detener (10 min), y duty-cycled (15 min). Guardar en C_selfheating_tabla.md.

C4. Gráfica de la serie de 60 s con las transiciones marcadas con líneas verticales → C_fig9_selfheating_serie.png (300 dpi, 3.2 × 2.4 in).

C5. Si existe git log del cambio a duty-cycle en display/ring_display.py, anotar el commit y la fecha.

D. Evaluación del detector de anomalías y del pronóstico (sección 4.4, Tablas 3 y 4)

D1. Escribir D_eval_anomalias.py que, sobre B_lecturas.csv, ejecute offline:

Baselines: umbral fijo (usar los umbrales configurados en alertas o, si no hay, ±2σ del dataset completo) y z-score rodante (ventana 60 muestras).
Etapa 1 (EWMA z-score) y etapa 2 (Isolation Forest) importando el código real de ml/anomaly.py, no reimplementándolo.
Conjunto de prueba: segmentos de comportamiento normal (sin alertas ni brechas) en los que se inyectan anomalías sintéticas de tres familias: escalones (±2, ±4, ±8 °C; ±5, ±10, ±20 %HR), rampas (0.05–0.5 °C/min durante 10–60 min) y picos de 1–3 muestras. Mínimo 30 inyecciones por familia, semilla fija.
Reportar por detector y por familia: precisión, recall, F1, retardo medio de detección (muestras) y tiempo de CPU por ciclo en la CM5 (medir con time.perf_counter).
Además, métricas de la etapa 2 en función del número de muestras de entrenamiento (100, 200, 500, 1000) para justificar el hand-over en 200.
Salida: D_tabla3_anomalias.csv y D_tabla3_anomalias.md.

D2. Escribir D_eval_forecast.py: evaluación rolling-origin sobre B_lecturas.csv con el horizonte real del sistema, comparando persistencia vs. Holt damped (importando ml/forecast.py). Reportar MAE y RMSE por variable, y separados por confianza_baja = verdadero/falso. Salida: D_tabla4_forecast.csv y .md.

D3. Registrar el pico sintético de 45 °C que ya se probó: buscar en ml_estado / logs (journalctl -u blackorbs-v2-ml) la marca de tiempo y el resultado (critico) → D_pico_sintetico.md.

D4. Medir consumo de recursos del servicio ML en la CM5: CPU % y RAM del proceso durante 10 ciclos (ps/psutil), y tiempo de entrenamiento del Isolation Forest → D_recursos_ml.md.

E. Evaluación de la interfaz de lenguaje natural (sección 4.5, Tablas 5 y 6)

E1. Exportar la tabla consultas_ia completa a E_consultas_ia.csv (pregunta, proveedor, modelo, tools invocadas, resultados de tools, respuesta, latencia si está guardada, timestamp).

E2. Escribir E_benchmark_chat.py que envíe a POST /chat un banco de 25 preguntas (5 por intención: estado actual; estadísticas de un periodo; comparación entre periodos; recuerdo de alertas/anomalías; fuera de alcance o sin datos), cada una 3 veces por proveedor (OpenAI y Claude; si OpenAI sigue sin créditos, registrarlo y correr solo Claude). Para cada respuesta registrar:

tools invocadas y argumentos;
si son las esperadas (tool-selection accuracy);
todos los números que aparecen en la respuesta y si cada uno coincide (±redondeo) con algún valor devuelto por las tools (fidelidad numérica; cualquier número sin respaldo = alucinación);
en los casos sin datos, si la respuesta declara explícitamente la ausencia;
latencia end-to-end (envío → respuesta completa) y número de tool calls.
Salida: E_tabla6_grounding.csv/.md y E_ejemplos_tabla5.md con 4 interacciones reales (una por intención) para la Tabla 5.
F. Tolerancia a fallos, alertas y potencia (sección 4.6)

F1. Prueba de desconexión: documentar el procedimiento para desconectar el uplink (Tailscale/WiFi) durante ≥ 2 h y, después, verificar con SQL que no faltan lecturas, que ml_estado siguió actualizándose y que se generaron alertas si aplicó. Indicar si las notificaciones generadas durante el corte se reintentan o solo quedan registradas. Salida: F_desconexion.md. (Si el usuario prefiere, dejar solo el script F_verificar_desconexion.py y que él ejecute la desconexión física.)

F2. Fuga de file descriptors: recuperar del journalctl -u blackorbs-v2-sensor la primera aparición de Errno 24 y confirmar el commit del with SMBus(...). Si existe un watchdog/heartbeat (alerta cuando la última lectura es más antigua que k intervalos), describirlo; si no existe, indicarlo → F_fd_leak.md.

F3. Reinicio por Piper: extraer del journal las líneas -- Boot -- y la actividad /tts de ~21 s antes, con timestamps → F_piper_reboot.md.

F4. Latencia de alertas: verificar estado de credenciales de Twilio/Telegram/email (probar un envío). Si funcionan, medir sobre ≥ 20 eventos el tiempo desde el timestamp de la lectura hasta la entrega por canal → F_latencia_alertas.md.

F5. Potencia con el servicio ML activo: no es medible desde software; dejar instrucciones para medir con un medidor USB/DC durante 1 h con todos los servicios corriendo → plantilla en F_potencia.md.

G. Verificaciones bibliográficas (no van en el dispositivo; para el autor)

G1. Confirmar las celdas "Partial" de la Tabla 1 contra los artículos citados (Hassan 2020, Medagedara 2024, Roostaei 2023, Halenár 2025, Dera 2026, Hidalgo-Castelo 2026).

G2. Confirmar la fuente real de la cita "priorización de eventos (Zhang et al., 2021)" del v16; en la lista solo existe Zhang y Tao (2021).

G3. Evidencia socio-técnica de planta (sección 5.1): número de alertas atendidas, tiempo de reacción antes/después, comentarios del personal.

Entrega

Comprimir articulo_datos/ (CSV, MD, PNG y scripts) y pasármela; con eso completo las Tablas 3, 4, 5, 6 y 7, regenero las Figuras 8 y 9, y sustituyo todos los marcadores amarillos del artículo.
