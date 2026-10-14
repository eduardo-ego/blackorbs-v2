# C3 — Autocalentamiento por fase (temperatura)

Ventanas usadas (hora local America/Mexico_City) — ver justificación en
`C1_transiciones_display.md`.

| Fase | Media (°C) | Desv. std (°C) | N muestras | Pendiente (°C/min) |
|---|---|---|---|---|
| Línea base (display off) | 28.99 | 0.23 | 15 | -0.029 |
| Animación continua (15 min) | 30.12 | 0.61 | 14 | +0.134 |
| Tras detener (10 min) | 30.61 | 0.48 | 10 | -0.135 |
| Duty-cycled post-corrección (15 min) | 29.18 | 0.29 | 15 | -0.043 |

Pendiente calculada por regresión lineal (mínimos cuadrados) de temperatura vs. minutos transcurridos dentro de cada ventana.
