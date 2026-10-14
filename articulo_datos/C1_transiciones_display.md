# C1 — Transiciones start/stop del servicio blackorbs-v2-display

Fuente: `journalctl -u blackorbs-v2-display --no-pager -o short-iso` (journal persistente, sin
límite de `--since`; se confirmó con `journalctl --list-boots` que el journal cubre desde
2025-04-30, por lo que esta es la **historia completa** del servicio, no solo una ventana reciente).

Hallazgo clave: el servicio **solo tiene actividad registrada el 2026-08-23** (día de la prueba) y
luego arranca una vez más tras un reinicio del sistema el 2026-09-06, sin ningún stop intermedio
(sigue `active running` hasta hoy, 2026-09-06). No hay una "re-prueba post-corrección" con su propio
ciclo on/off/on — la corrección se aplicó y el servicio quedó corriendo continuamente desde entonces.

## Línea de tiempo completa (hora local America/Mexico_City, UTC-6)

| # | Evento | Timestamp local | Duración del run anterior | CPU consumida en ese run |
|---|---|---|---|---|
| 1 | Started | 2026-08-23T16:17:28-06:00 | — (primer arranque histórico del servicio) | — |
| 2 | Stopped | 2026-08-23T16:17:56-06:00 | 28 s | 23.332 s |
| 3 | Started | 2026-08-23T16:17:56-06:00 | — | — |
| 4 | Stopped | 2026-08-23T16:18:20-06:00 | 24 s | 16.955 s |
| 5 | Started | 2026-08-23T16:18:20-06:00 | — | — |
| 6 | Stopped | 2026-08-23T16:19:12-06:00 | 52 s | 31.868 s |
| 7 | Started | 2026-08-23T16:19:12-06:00 | — | — |
| 8 | Stopped | 2026-08-23T16:40:52-06:00 | 21 min 40 s | 10 min 21.049 s (≈47.8% duty) |
| 9 | Started | 2026-08-23T16:59:27-06:00 | (18 min 35 s sin servicio) | — |
| — | *(reinicio del sistema)* | boot entre 2026-08-23 y 2026-09-06 | servicio corrió sin stop registrado hasta el reinicio | — |
| 10 | Started (post-reinicio) | 2026-09-06T13:21:47-06:00 | — | — |
| — | *(sigue activo)* | hasta el momento de esta extracción, 2026-09-06 ~20:06 | — | — |

## Interpretación propuesta para las ventanas del experimento (sección 4.3)

No hay etiquetas explícitas en el journal que digan "esto es la prueba de animación continua" —
se infiere por duración y CPU consumida. **El autor debe confirmar** que esta interpretación
corresponde a lo que realmente se probó ese día:

- **Línea base (display apagado):** el servicio nunca había arrancado antes de las 16:17:28 (ver
  arriba), así que el intervalo previo, p. ej. **16:02:28–16:17:28**, sirve como línea base con
  display off.
- **Animación continua (~15 min):** los tres reinicios rápidos (16:17:28–16:19:12, corridas de
  24–52 s) parecen pruebas manuales cortas, no la corrida de 15 min formal. La corrida larga
  **16:19:12 → 16:40:52 (21.7 min, ~48% de CPU sostenido)** es la única candidata de duración
  suficiente para la prueba de "animación continua" — se sugiere usar sus primeros 15 min:
  **16:19:12–16:34:12**.
- **Tras detener (10 min):** inmediatamente después del stop de esa corrida:
  **16:40:52–16:50:52**.
- **Duty-cycled (post-corrección, ~15 min):** desde el arranque final de ese día,
  **16:59:27–17:14:27** (con el código actual de `ring_display.py`, que ya implementa
  duty-cycle — un frame y a dormir `REFRESCO_SEGUNDOS`, ver `A_parametros_ml.md`).

Estas cuatro ventanas se usan en `C2_exportar_ventanas.py` (±60 min alrededor de cada transición,
por instrucción original) y en `C_selfheating_tabla.py` (estadística dentro de cada ventana
específica arriba). Si el autor tiene notas de laboratorio de esa sesión que precisen mejor cuál
corrida fue cuál, hay que corregir las ventanas en `C_selfheating_tabla.py` antes de generar la
Tabla del artículo.
