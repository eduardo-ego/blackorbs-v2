# A2 — Herramientas (function calling), system prompt y parámetros del chat LLM

Fuente: `api/Controllers/chatController.js` (nota: la ruta real tiene `Controllers/` con mayúscula,
no `controllers/` como decían las instrucciones — el repo usa esa convención en todo `api/`).

## Herramientas (idénticas para ambos proveedores, solo cambia el formato de declaración)

Todas son de solo lectura sobre datos ya calculados por el sensor o el servicio de ML; el LLM nunca
deriva anomalías/forecast por sí mismo (comentario explícito en el código).

1. **`get_estado_actual`**
   - Descripción: "Estado actual calculado por el sistema de ML: mood (contento/atencion/critico),
     score de anomalía y forecast vigente."
   - Parámetros: `{}` (ninguno).
   - Implementación: `SELECT * FROM ml_estado WHERE device_id = ?`; si no hay fila, devuelve
     `{ mood: 'contento', message: 'Aún no hay estado de ML calculado.' }`. Añade `hora_local`
     (America/Mexico_City) calculado desde `updated_at`.

2. **`get_ultima_lectura`**
   - Descripción: "Última lectura cruda del sensor (temperatura, humedad, presión, timestamp)."
   - Parámetros: `{}` (ninguno).
   - Implementación: `SELECT * FROM lecturas WHERE device_id = ? ORDER BY timestamp DESC LIMIT 1`,
     con `hora_local` añadido.

3. **`get_historial_lecturas`**
   - Descripción: "Lecturas del sensor en los últimos N minutos, para preguntas sobre tendencias."
   - Parámetros: `{ minutos: number }` — "Ventana de tiempo en minutos, por defecto 60" (el default
     de 60 se aplica en el código, `getHistorialLecturas(deviceId, minutos = 60)`, no en el schema).
   - Implementación: `SELECT temperature, humidity, pressure, timestamp FROM lecturas WHERE
     device_id = ? AND timestamp >= datetime('now', '-N minutes') ORDER BY timestamp ASC`, con
     `hora_local` por fila.

4. **`get_alertas_recientes`**
   - Descripción: "Alertas recientes generadas por el sistema."
   - Parámetros: `{ limit: number }` — "Cuántas alertas traer, por defecto 10" (default aplicado en
     código, `getAlertasRecientes(limit = 10)`).
   - Implementación: `SELECT * FROM alertas ORDER BY timestamp DESC LIMIT ?`, con `hora_local` por
     fila.

Declaración por proveedor (mismo `TOOLS_SPEC` base, dos vistas):
- OpenAI: `{ type: 'function', function: { name, description, parameters } }`.
- Claude: `{ name, description, input_schema: parameters }`.

## System prompt (idéntico para ambos proveedores, texto literal)

```
Eres el asistente conversacional de este dispositivo de monitoreo ambiental.
No tienes forma de medir ni calcular nada tú mismo: toda la inteligencia (detección de
anomalías y forecasting) ya la calculó un servicio de Machine Learning aparte y vive en
las herramientas que tienes disponibles. Tu único trabajo es: (1) entender lo que pide
el usuario en lenguaje natural, (2) llamar a las herramientas necesarias para obtener
los datos ya calculados, y (3) responder de forma breve, clara y en español, sin inventar
números que no vengan de una herramienta. Si mencionas una hora, usa siempre el campo
"hora_local" de la herramienta (zona horaria del dispositivo, America/Mexico_City) — nunca
el campo "timestamp"/"updated_at", que está en UTC y confundiría al usuario.
```

## Modelos, tokens y límite de iteraciones

| | OpenAI | Claude |
|---|---|---|
| Modelo | `gpt-4o` | `claude-opus-5` |
| `max_tokens` | **no se especifica** en la llamada (`openai.chat.completions.create` sin `max_tokens`) → default del proveedor | `1024` (explícito en `claude.messages.create`) |
| `temperature` | `0.2` | no se especifica (default del proveedor) |
| Límite de iteraciones del loop tool-use | `for (let i = 0; i < 4; i++)` → **4 iteraciones máximo** | `for (let i = 0; i < 4; i++)` → **4 iteraciones máximo** |
| Comportamiento si se agota el loop sin respuesta final | devuelve el string fijo `"No pude obtener una respuesta clara, intenta reformular la pregunta."` | igual |

## Persistencia de la conversación (`consultas_ia`)

`INSERT INTO consultas_ia (device_id, modelo, prompt, respuesta) VALUES (...)`. Importante para
E1/E2: la tabla real **solo guarda** `device_id`, `modelo` (= `"openai"` o `"claude"`, el nombre del
*proveedor*, no el modelo específico como `gpt-4o`/`claude-opus-5`), `prompt`, `respuesta` y
`timestamp` (autogenerado). **No existen columnas para**: tools invocadas, argumentos de las tools,
resultados de las tools, ni latencia. Esa información solo existe en tiempo de ejecución (dentro de
`responderConOpenAI`/`responderConClaude`) y no se persiste — para la Tabla 6 (E2) hay que
capturarla en el propio script de benchmark (`E_benchmark_chat.py`), no se puede reconstruir después
desde la base de datos. Ver `E_consultas_ia.csv` para lo que sí se puede exportar hoy.

## Manejo de errores relevante para el artículo (sección 4.6 / fiabilidad del chat)

`mensajeDeError(err)` en `chatController.js` traduce errores del proveedor a mensajes en español:
falta de API key, `insufficient_quota`/sin créditos, 401 (clave inválida), 429 (límite de uso). Esto
explica por qué, si OpenAI no tiene créditos (mencionado en la instrucción E2), el endpoint
`/chat` con `provider=openai` devuelve HTTP 500 con
`{ error: 'La cuenta de este proveedor no tiene créditos/facturación activa.' }` en vez de lanzar una
excepción no controlada.
