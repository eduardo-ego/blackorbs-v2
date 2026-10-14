# D3 — Pico sintético de 45 °C

**No se encontró evidencia de una lectura (real o inyectada) de 45 °C en ningún lado.**

Búsquedas realizadas:

- `B_lecturas.csv` completo (20 484 lecturas, todo el dataset): **la temperatura máxima registrada
  es 42.90 °C**, el 2026-08-27 09:40:09 (hora local), no 45 °C. No hay ninguna fila con
  `temperature >= 44`.
- `journalctl -u blackorbs-v2-ml` (historia completa del servicio, 20 552 líneas): no aparece
  ningún valor de 45 en el log ni mención textual de "pico"/"sintético"/"synthetic".
- `journalctl` general del sistema (todos los servicios) filtrando por "45": no hay coincidencias
  relevantes (solo ruido de NetworkManager y timestamps que casualmente contienen "45").
- `~/.bash_history` (2000 líneas retenidas, hasta 2026-08-26 22:47): no hay comandos `curl`/scripts
  relacionados con enviar una lectura de 45 °C a `/data` o `/ml/update`.

## Hallazgo relacionado (no es el pico de 45 °C, pero es relevante para la sección 4.4)

Al arrancar el servicio `blackorbs-v2-ml` por primera vez el 2026-08-23 10:56:34 (ver journal),
el sistema reportó **`mood=critico` de forma sostenida durante muchos minutos consecutivos**
(10:56:34 hasta más allá de las 11:54, con lecturas reales de temperatura normales, ~29 °C — ver
tabla en la sección de verificación de este archivo). Esto **no corresponde a una anomalía real en
los datos**, sino a un artefacto de arranque en frío: con pocas lecturas históricas cargadas justo
al iniciar el servicio, Isolation Forest se entrena con una muestra pequeña y poco representativa,
lo que produce una calibración de percentiles (p5/p15) inestable y falsos positivos sostenidos.
Vale la pena mencionarlo en el artículo como una limitación conocida del arranque en frío del
detector de etapa 2, independiente del caso del pico de 45 °C que pedía la instrucción original.

## Conclusión para el artículo

La prueba de "pico sintético de 45 °C" descrita en las instrucciones **no dejó rastro verificable
en este dispositivo** con las fuentes disponibles (base de datos, journal, bash history). Puede
haberse hecho: (a) en una sesión anterior cuyo log ya rotó fuera de la ventana retenida (aunque el
journal cubre desde abril 2025, así que esto es poco probable), (b) mediante un método que no deja
rastro en estas fuentes (p. ej. una llamada manual a `POST /ml/update` con un `anomaly_score`
fabricado directamente, sin pasar por una lectura de temperatura real — eso no dejaría huella en
`lecturas`), o (c) el dato de "45 °C" es un plan para una prueba que aún no se ha ejecutado.
**Se necesita que el autor confirme cómo y cuándo se hizo esa prueba**, o bien se ejecute de nuevo
(p. ej. insertando manualmente una fila de prueba vía `POST /data` con `temperature: 45`, con el
servicio ML corriendo, y capturando el resultado en `ml_estado`/journal en el momento) para poder
documentarla en la sección 4.4.
