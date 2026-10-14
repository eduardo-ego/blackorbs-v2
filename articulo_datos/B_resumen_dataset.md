# B2 — Resumen del dataset (`lecturas`, device_id=ORBE_001)

- Primera lectura: **2026-08-22T23:35:48.724000+00:00**
- Última lectura: **2026-09-07T02:04:45.801000+00:00**
- Total de lecturas: **20484**
- Días de operación (última - primera): **15.10 días**
- Intervalo de muestreo efectivo (mediana de diferencias entre timestamps consecutivos):
  **60.6 s** (nominal configurado: 60 s, ver `A_parametros_ml.md`)

> Nota: "días de operación" aquí es el rango temporal cubierto por timestamps, no tiempo con el
> sensor efectivamente reportando sin interrupciones — ver `B_brechas.csv`/`B_brechas.md` para el
> uptime real.

## Estadística descriptiva

| Variable | Media | Desv. std | Mín | Máx | P5 | P50 | P95 |
|---|---|---|---|---|---|---|---|
| Temperatura (°C) | 25.58 | 4.96 | 17.44 | 42.90 | 18.47 | 25.40 | 32.73 |
| Humedad (%HR) | 62.40 | 14.13 | 29.98 | 89.57 | 42.38 | 60.45 | 86.15 |

(Desviación estándar muestral, ddof=1. Calculado sobre valores no nulos únicamente.)
