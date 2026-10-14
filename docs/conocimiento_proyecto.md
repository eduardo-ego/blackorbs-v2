# Black Orbs — Conocimiento del proyecto

> Documento fuente para redactar documentación técnica y el artículo de tesis. Consolida todo lo aprendido durante el diseño, construcción y depuración del sistema v2. Última actualización: 2026-09-06.

## 1. Contexto general

**Black Orbs** es el proyecto de tesis de eduardo-ego: un dispositivo IoT de monitoreo ambiental construido sobre una Raspberry Pi CM5, desarrollado inicialmente hace ~2 años (v1) y rediseñado en 2026 (v2) para incorporar un núcleo de Machine Learning real.

Repositorio original v1: `eduardo-ego/blackorbs_device` (privado). El código v1 quedó respaldado en `/home/blackorbs/backup/` y fue completamente decomisionado (ver §7).

Repositorio de trabajo v2: `/home/blackorbs/blackorbs-v2/`.

## 2. Arquitectura v1 (histórica, ya no en producción)

- Sensor BME680 → `temperature.service` leía temperatura/humedad/presión y hacía POST a una API Express local.
- La Pi actuaba como su propio punto de acceso WiFi (`check_wifi_nm.service`).
- Persistencia en MongoDB remoto (ej. Atlas — no accesible localmente, sin mongod/mongosh en el dispositivo).
- Las rutas de la API llamaban directamente a APIs de LLM (OpenAI/DeepSeek/Mistral) sobre los números crudos del sensor para "análisis".
- Notificaciones vía Twilio (WhatsApp/Telegram/email).
- Animación de "ojos" en un display OLED, duplicada en 3 archivos distintos.
- Existía además `monitoring/monitoring.py`, un script casi duplicado que usaba un sensor distinto (SHT85) sin servicio systemd asociado — nunca quedó claro si seguía vigente, pero resultó ser una pista clave: el hardware real no era el BME680 que asumía el resto del código v1 (ver §6.5).

### Decisión de no tocar v1

Se decidió no refactorizar el código v1 y en su lugar diseñar una v2 desde cero, con mejor arquitectura, dejando v1 intacto como referencia histórica (después decomisionado, ver §7).

## 3. Motivación del rediseño (v1 → v2)

**Problema identificado:** usar un LLM para interpretar directamente datos numéricos crudos de sensores es difícil de evaluar rigurosamente ante un comité de tesis. Un modelo de ML real, con métricas medibles, es una base mucho más sólida.

**Decisión de arquitectura:**
- El **núcleo de ML** hace el trabajo analítico real: detección de anomalías y pronóstico/predicción sobre la serie temporal de datos del sensor.
- El **LLM queda relegado a una capa de interfaz en lenguaje natural**: traduce comandos NL del usuario en acciones estructuradas, y traduce las salidas del sistema/ML en mensajes NL para notificaciones y chat. Ya no interpreta directamente los datos crudos del sensor.

**Decisiones adicionales tomadas por el usuario:**
- Empezar de cero, sin migrar datos históricos de Mongo.
- Umbrales de anomalía **auto-aprendidos** (basados en percentiles/desviación estándar), no fijos manualmente.
- La inferencia de ML corre en la misma Pi — no hay servidor separado; API, base de datos y sensor viven en un solo dispositivo CM5.

## 4. Arquitectura v2 — visión general

Todo vive en `/home/blackorbs/blackorbs-v2/`, organizado en componentes independientes (cada uno con su propio entorno virtual de Python cuando aplica), comunicándose por HTTP/Socket.IO sobre `localhost`.

```
blackorbs-v2/
├── api/       Express + Socket.IO + SQLite (Node.js)
├── ml/        Servicio de análisis (Python: scikit-learn, statsmodels, pandas)
├── sensor/    Lectura del sensor físico (Python)
├── display/   Animación del OLED (Python: luma.oled, pillow)
└── data/      Base de datos SQLite
```

### 4.1 API (`api/`)

- Express + Socket.IO. MongoDB fue reemplazado por **SQLite** (`better-sqlite3`), archivo en `data/blackorbs.db`, esquema en `api/db/schema.sql`.
- Tablas: `lecturas`, `alertas`, `consultas_ia`, `ml_estado`.
- Rutas/controladores portados 1:1 desde v1: `dataController`, `alertController`.
- Nuevos controladores:
  - `mlController`: recibe el estado calculado por el servicio de ML en Python, hace upsert de `ml_estado`, emite el evento Socket.IO `mlUpdate`.
  - `chatController`: capa de LLM puramente de lenguaje natural — usa function-calling (OpenAI y Claude) con herramientas de solo lectura sobre `ml_estado`/`lecturas`/`alertas`. **Nunca calcula anomalías por sí mismo.** Emite el evento Socket.IO `chatMood` para el estado "pensando" de la interfaz.
- Verificado end-to-end (ingesta de datos, persistencia en SQLite, flujo ml/update → socket).

### 4.2 Machine Learning (`ml/`)

Entorno virtual Python propio (scikit-learn, statsmodels, pandas).

- **`anomaly.py`** — detector híbrido:
  - Desde la primera lectura: detector EWMA/z-score.
  - Al alcanzar ≥200 lecturas (`config.MIN_LECTURAS_MODELO_APRENDIDO`): transición a **Isolation Forest**.
  - Las severidades se derivan de percentiles/desviación estándar, no están hardcodeadas.
  - `normalidad_pct` (0-100): derivado del z-score EWMA o del rango percentil del score de Isolation Forest respecto a su propio historial.
- **`forecast.py`** — pronóstico:
  - Con menos de ~30 puntos: forecast de persistencia (naive).
  - Con más de ~30 puntos: **suavizado exponencial de Holt con tendencia amortiguada** (damped trend).
  - Expone un flag `confianza_baja` → mostrado en la UI como `forecast_confianza` ("alta"/"baja").
- **`service.py`** — corre el ciclo cada `CICLO_SEGUNDOS` (default 60s) y hace POST del resultado a `/ml/update` de la API.
- Probado manualmente: un pico sintético de 45°C contra una línea base de ~24°C fue correctamente marcado como `critico`.
- Variables monitoreadas: `["temperature", "humidity"]` — sin presión (ver §6.5, el hardware real no mide presión).

### 4.3 Sensor (`sensor/`)

- Entorno virtual propio; reinstala `bme680`/`smbus2`/`requests`, aunque en la práctica solo se usan `smbus2` y `requests`.
- `read_loop.py`: lee un sensor **SHT85** en la dirección I2C `0x44` (soft-reset + lectura sobreamuestreada, misma técnica que el antiguo `monitoring.py` de v1). Hace POST a la API cada `SENSOR_INTERVALO_SEGUNDOS` (default 60s).
- Sin calibración: los offsets del antiguo `monitoring.py` (temp -9.7, hum +11.3) se descartaron deliberadamente — v2 arranca sin calibrar (offset 0), pendiente de recalibrar contra un termómetro de referencia si se requiere.

### 4.4 Display (`display/`)

- Reemplaza tanto la animación de "ojos" de v1 como la pantalla de arranque "BLACK ORBS".
- `ring_display.py`: dibuja un anillo etéreo (sin texto/branding) en el mismo OLED SSD1306 físico (i2c bus 6, dirección 0x3C).
- El estilo del anillo (grosor / anillo simple vs. doble) refleja `ml_estado.mood`, leído **directamente de SQLite** (sin HTTP ni autenticación de por medio).
- Debajo del anillo se muestra temperatura y humedad en vivo.
- Animación de arranque: el anillo se forma desde el centro, una sola vez al iniciar el servicio.
- **Importante:** el ciclo de refresco es *duty-cycled*, no continuo (ver hallazgo en §6.6 — la animación continua calentaba el sensor).

### 4.5 Frontend (`api/public/index.html`)

- Reconstruido a partir de un artifact de Claude ("anillo etéreo"): mood ring donde `contento` = verde/calmado, `atencion` = amarillo, `critico` = rojo/pulsante, `pensando` = violeta/rápido.
- El CSS se tomó directamente del artifact; se eliminó el script del sandbox de iframe de claude.ai porque corre standalone.
- **Nota de diseño:** los Artifacts no pueden usarse como frontend en vivo aquí — el CSP estricto bloquea WebSocket/fetch arbitrario hacia un dispositivo LAN. El artifact solo sirvió como fuente de diseño/código, portado a la página estática servida por Express.
- Panel de chat conectado a `/chat`.
- Tema oscuro + glassmorphism/neumorphism (`--bg: #08090c`, blobs de brillo de baja opacidad). El `.card` exterior del anillo se eliminó para que flote libre; solo el panel de chat conserva la tarjeta de vidrio.
- Selector de proveedor de LLM: un ícono circular fijo arriba a la izquierda, cicla entre OpenAI/Claude al hacer clic (letra + tinte por proveedor).
- Barra de progreso delgada + porcentaje debajo del anillo para `normalidad_pct`, más una etiqueta de confianza junto al texto de pronóstico.
- Respuestas de voz: `speechSynthesis` nativo del navegador (es-MX), activable/desactivable con un botón 🔊/🔇 (ver §6.7 — se intentó TTS neuronal server-side y se revirtió).

## 5. Proveedores de LLM

- Se descartaron DeepSeek y Mistral por completo; se usan solo **OpenAI + Claude** en paralelo.
- `chatController.js` soporta ambos (`provider: "openai"|"claude"` en el body del POST, default `openai`).
- Integración con Claude vía `@anthropic-ai/sdk`, loop manual de tool-use, modelo `claude-opus-5`.
- **Estado verificado:**
  - **Claude:** funcionando end-to-end. Llama correctamente `get_estado_actual`/lee `lecturas` vía tool-calling, responde en lenguaje natural, nunca inventa números cuando no hay datos. Registra en `consultas_ia` con `modelo='claude'`.
  - **OpenAI:** la key autentica correctamente pero la cuenta no tiene créditos activos (`insufficient_quota`/`credit_balance_exhausted`). `chatController` distingue explícitamente entre "cuenta sin créditos", "key inválida", "falta configurar key" y "rate limited". Pendiente: activar facturación en platform.openai.com.
- Twilio/Telegram/Email siguen usando credenciales de ~2 años de antigüedad heredadas de v1, sin probar, probablemente vencidas.

## 6. Hallazgos e incidentes de validación

Esta sección es material directo para la sección de metodología/validación/limitaciones del artículo: son hallazgos concretos, medidos y reproducibles, no solo bugs corregidos.

### 6.5 El hardware real no es el que asumía v1

Un escaneo del bus I2C 6 encontró solo dos dispositivos: `0x3c` (OLED SSD1306) y `0x44` (sensor tipo SHT85, temperatura/humedad, **sin presión**). Esto coincide con `monitoring/monitoring.py` de v1, no con `temperature/main_temp.py` (que asumía un BME680).

**Consecuencias:**
- El servicio v1 `testing_temp.service` (código BME680, corriendo como root cada 10s, publicando hacia una IP obsoleta `192.168.1.164` que ya no correspondía a esta Pi) fue detenido y deshabilitado — no llegaba a ningún lado y además competía por el bus I2C con el lector de v2.
- El campo `pressure` es opcional de extremo a extremo en v2 (`dataController.js` acepta presión ausente/null; `ml/config.py` solo monitorea `["temperature", "humidity"]`).

### 6.6 El display OLED calienta medible mente el sensor de temperatura

La primera versión de `ring_display.py` animaba continuamente (5-25 fps, respiración/rotación del anillo), manteniendo el CPU sostenido en 50-80% de un núcleo.

**Prueba controlada (encender/apagar/encender) vía consultas directas a SQLite alrededor de los tiempos de inicio/parada del servicio de display:**
- Línea base (display apagado, como había estado todo el día): ~29.0°C.
- Tras ~15 min de animación continua: subida a una meseta de ~30.6-31.0°C (+1.3 a +2°C).
- Tras detener la animación: regreso a ~30.0°C en ~10 min.

Esto confirma causalidad, no coincidencia. El usuario confirmó que el sensor SHT85 tiene separación física de la placa principal, lo que apunta a la carga sostenida de CPU/SoC como mecanismo (no proximidad física al OLED).

**Corrección validada:** el loop de display se reescribió para ser *duty-cycled* en vez de animado continuamente — despierta una vez cada `DISPLAY_REFRESCO_SEGUNDOS` (default 60s, igual al intervalo del sensor), dibuja un frame estático y duerme (0% de CPU medido entre refrescos, contra 50-80% antes). Reprueba de 15 min post-corrección: media de 29.14°C, plana, sin tendencia ascendente — igual a la línea base original.

**Implicación metodológica:** si la animación del display se vuelve más elaborada/rápida en el futuro, hay que repetir esta prueba de comparación antes/después vía SQLite (parar/iniciar `blackorbs-v2-display`, comparar medias de `lecturas.temperature` entre transiciones) antes de asumir que es segura — es una fuente de sesgo real y antes desconocida sobre el sensor primario del que depende una tesis sobre detección de anomalías.

### 6.7 TTS neuronal (Piper) probado y revertido — riesgo de crash del dispositivo

Se intentó mejorar el `speechSynthesis` del navegador con TTS neuronal real vía **Piper** (componente `tts/`, entorno virtual propio, ejecutaba `piper -m <modelo> -f -` desde `ttsController.js`/`POST /tts`). Funcionaba correctamente de forma aislada.

En producción se correlacionó con **reinicios completos de la Raspberry Pi CM5** — `journalctl` mostró una línea `-- Boot --` nueva ~21 segundos después de actividad relacionada con `/tts`, es decir, el dispositivo completo se reiniciaba, no solo el proceso de Node. Causa más probable: el runtime ONNX de Piper agotando la RAM limitada de la CM5.

**Se revirtió por completo:** `hablar()` en `index.html` volvió a `SpeechSynthesisUtterance` nativo del navegador (es-MX, sin llamada al backend). Se eliminaron `ttsController.js`/`ttsRoutes.js` y su registro en `api/app.js`. Se borró todo el directorio `tts/` (venv + binario de Piper + modelo de voz, 311MB).

**Implicación:** no se debe volver a sugerir correr Piper (o TTS similar basado en ONNX runtime) directamente en la CM5. Si se quiere TTS neuronal de nuevo, debe correr fuera del dispositivo (servidor separado), dado este historial de crashes.

### 6.8 Fuga de file descriptors causó una brecha de datos de ~15.4 horas

`leer_sensor()` en `sensor/read_loop.py` abría un `smbus2.SMBus(I2C_BUS)` nuevo en cada ciclo (60s) sin cerrarlo nunca — cada lectura filtraba un file descriptor hacia `/dev/i2c-6`.

Tras ~1024 ciclos (el límite por defecto de FDs por proceso en Linux) el proceso lanzó `OSError: [Errno 24] Too many open files` y falló silenciosamente en cada ciclo posterior — el servicio seguía "activo" en systemd porque el loop nunca crasheaba, solo el try/except dentro de `leer_sensor()` absorbía el error.

Confirmado vía `ls /proc/<pid>/fd | grep i2c | wc -l` = 1021 antes de la corrección.

**Resultado:** una brecha real e irrecuperable en `lecturas` entre las **2026-08-24 05:26am y 8:51pm** (hora local), detectada porque el usuario notó que la última lectura del dashboard estaba congelada en las 5am. Existían además dos brechas menores previas (124 min y 13 min el 2026-08-23), no relacionadas con este bug.

**Corrección:** ambas aperturas de `smbus2.SMBus(I2C_BUS)` (`leer_sensor()` y el bus de `soft_reset` en `main()`) se envolvieron en `with ... as bus:` para garantizar el cierre del FD. Verificado: el conteo de FDs se mantiene plano en 3 tras múltiples ciclos.

**Implicación metodológica:** si un servicio que toca `/dev/i2c-*` u otros descriptores de archivo/socket en un loop parece "dejar de actualizarse silenciosamente" mientras systemd lo sigue mostrando activo, revisar `ls /proc/<pid>/fd | wc -l` contra `ulimit -n` antes de asumir que es un problema de hardware o de red — este modo de falla (fuga lenta de FDs, ~17h para manifestarse con un ciclo de 60s) es fácil de pasar por alto porque el proceso nunca muere.

## 7. Decomisión de v1 e infraestructura de despliegue

- Todo el código v1 (`/home/blackorbs/API`, `animation`, `monitoring`, `temperature`, `testing`, `splash`) se movió a `/home/blackorbs/backup/`; sus servicios (`eye_animation`, `splash`, `temperature`, `testing_temp`) fueron deshabilitados y detenidos.
- `nodered.service` también fue deshabilitado y detenido (Node-RED y su directorio de datos `.node-red` siguen instalados pero inactivos, no se eliminaron).
- **Servicios systemd de v2** (todos `User=blackorbs`, `Restart=always`/`RestartSec=3`, habilitados con `enable --now`, sobreviven reinicios):
  - `blackorbs-v2-api.service` — `node server.js` desde `api/`.
  - `blackorbs-v2-sensor.service` — Python del venv propio ejecutando `read_loop.py`.
  - `blackorbs-v2-ml.service` — Python del venv propio ejecutando `service.py`.
  - `blackorbs-v2-display.service` — Python del venv propio ejecutando `ring_display.py`.
  - `sensor`/`ml` declaran `After=`/`Wants=blackorbs-v2-api.service` pero dependen de `Restart=always` más que de una dependencia dura, ya que sus configs por defecto apuntan a `localhost:3001`.
  - Logs: `journalctl -u <nombre-del-servicio> -f`.
- **Tailscale** instalado y conectado (dispositivo visible como `botsandbytes`, IP de tailnet `100.93.81.6`) — permite acceso remoto a la app v2 para pruebas.
- **Pendiente (diferido explícitamente por el usuario):** estrategia de respaldo para el archivo SQLite.

## 8. Preguntas abiertas / pendientes

- Cantidad real de datos históricos disponibles (afecta la elección entre estadística clásica vs. modelo aprendido) — no resuelto aún de forma cuantitativa.
- Si la tesis apunta a un dominio/caso de uso específico o se mantiene como monitoreo ambiental de propósito general.
- Activar facturación de OpenAI para desbloquear esa vía del chat (Claude no requiere ninguna acción adicional).
- Probar y, si es necesario, renovar las credenciales de Twilio/Telegram/Email heredadas de v1.
- Recalibrar el sensor SHT85 contra un termómetro de referencia si se requiere precisión absoluta (actualmente offset 0, sin calibrar).
- Backup de la base de datos SQLite (diferido: "lo vemos luego").

## 9. Fase actual del proyecto (desde 2026-09-06)

El sistema v2 ya está construido y corriendo en producción. El foco actual del trabajo es:
1. **Documentación técnica** del sistema (arquitectura, componentes, decisiones de diseño).
2. **Artículo de tesis** — los incidentes de la §6 son candidatos naturales para una sección de metodología/validación/limitaciones, ya que son hallazgos medidos y reproducibles (no solo corrección de bugs), con datos de antes/después, causa raíz identificada y corrección verificada.
