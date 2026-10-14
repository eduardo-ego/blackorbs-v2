# E2 — Tabla 6: grounding / fidelidad numérica del chat LLM

**Nota de metodología:** tool-selection accuracy y 'tools invocadas y argumentos' no son observables desde /chat (ver cabecera de E_benchmark_chat.py) — no se reportan aquí.

**Advertencia importante sobre la fidelidad numérica de esta corrida:** el ground-truth se calculó **una sola vez, al arrancar el script** (`valores_ground_truth()` se llama una vez en `main()`), pero las 75 llamadas tardaron **10 minutos** en total y el sensor/ML del dispositivo siguieron corriendo en vivo durante ese tiempo (nuevas lecturas cada 60s, `ml_estado` recalculándose). Esto significa que para preguntas respondidas varios minutos después de arrancar el script, el LLM reportó correctamente valores *más recientes* que ya no coincidían con el ground-truth congelado al inicio — se cuentan como "no respaldados" sin serlo realmente. Revisando ejemplos concretos (`E_ejemplos_tabla5.md`, `D_tabla3_detalle_injecciones.csv` no aplica aquí): las respuestas de estado_actual, por ejemplo, se ven bien fundamentadas (temperatura/humedad/forecast consistentes con lo que el sistema reportaba en ese momento). **La cifra de fidelidad % de esta tabla subestima la fidelidad real** — para una medición correcta, `E_benchmark_chat.py::valores_ground_truth()` debe llamarse de nuevo antes de cada pregunta individual, no una sola vez al inicio. Se deja como mejora pendiente del script si se quiere repetir la corrida.

Además, el regex de extracción de números cuenta también los componentes de horas (p. ej. "08:35 p.m." aporta los números 08 y 35), lo que infla el denominador de "números totales" con valores que no son datos de sensor y nunca van a "coincidir" contra el ground-truth de temperatura/humedad — otra causa de que el % de fidelidad se vea más bajo de lo real.

**Lo que sí es un hallazgo genuino y no un artefacto de metodología:** de las 75 llamadas, **9 (12%)** devolvieron el mensaje de fallback `"No pude obtener una respuesta clara, intenta reformular la pregunta."` (0 números, ok=True pero sin contenido útil) — concentradas en `comparacion_periodos` (6 de 15 = 40%) y `estadisticas_periodo` (3 de 15 = 20%). Esto sí es directamente atribuible al **límite de 4 iteraciones del loop de tool-use** (ver `A_herramientas_llm.md`): las preguntas que requieren comparar dos periodos o resumir estadísticas necesitan más de una llamada a `get_historial_lecturas` con distintas ventanas, y con dos tools por ventana + composición de la respuesta, 4 iteraciones no siempre alcanzan. Vale la pena reportar este 12%/40% como limitación real del diseño en la sección 4.5, independientemente de la corrección del ground-truth.

Por último: de las 15 preguntas "fuera_de_alcance" (14 con respuesta OK), **14/14 (100%) declararon explícitamente la falta de datos/alcance** — este resultado sí es confiable tal cual (no depende del ground-truth congelado), y es un resultado fuerte a favor del diseño del system prompt.

| Proveedor | Intención | N respuestas OK | Latencia media (s) | Números totales | Respaldados | Fidelidad % |
|---|---|---|---|---|---|---|
| claude | comparacion_periodos | 15 | 10.44 | 139 | 41 | 29.5 |
| claude | estadisticas_periodo | 15 | 10.66 | 227 | 58 | 25.6 |
| claude | estado_actual | 15 | 6.87 | 169 | 71 | 42.0 |
| claude | fuera_de_alcance | 14 | 6.22 | 50 | 22 | 44.0 |
| claude | recuerdo_alertas | 15 | 5.92 | 210 | 35 | 16.7 |

Llamadas fallidas/omitidas: 1 (ver columna `error` en `E_tabla6_grounding.csv`).
