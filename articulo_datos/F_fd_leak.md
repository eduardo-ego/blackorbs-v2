# F2 — Fuga de file descriptors (Errno 24)

## Primera aparición

```
journalctl -u blackorbs-v2-sensor --no-pager -o short-iso | grep "Errno 24"
```

**Primera línea:** `2026-08-24T05:27:55-06:00 ... OSError: [Errno 24] Too many open files:
'/home/blackorbs/blackorbs-v2/sensor/calibration.json'`

Un minuto después empieza a fallar también el propio bus I2C: `OSError: [Errno 24] Too many open
files: '/dev/i2c-6'`, repitiéndose cada ciclo (60 s) de forma continua durante horas.

**Correlación directa con B3:** esta primera falla (05:27:55 local) ocurre 1 minuto después de la
última lectura exitosa antes de la brecha grande documentada en `B_brechas.md`
(**2026-08-24 05:26:54–20:51:31 local, 924.6 min**). Es decir, **la fuga de file descriptors es la
causa raíz confirmada de esa brecha**: el proceso `sensor` se quedó sin descriptores disponibles y
no pudo seguir abriendo `calibration.json` ni `/dev/i2c-6`, dejando de reportar lecturas durante
~15.4 horas hasta que algo (probablemente un reinicio del servicio o del sistema) liberó los
descriptores.

## Commit del fix (`with SMBus(...)`)

**No se puede confirmar un commit** — como se documenta en `C5_git_duty_cycle.md`, el directorio
`blackorbs-v2/` completo no está bajo control de versiones en este dispositivo (el `.git` presente
tiene su raíz en `/home/blackorbs` y no incluye ningún archivo del proyecto). Lo que sí se puede
confirmar es el **estado actual del código**: `sensor/read_loop.py` ya usa
`with smbus2.SMBus(I2C_BUS) as bus:` como gestor de contexto tanto en `leer_sensor()` (línea 45)
como en `main()` (línea 76), lo que cierra el descriptor del bus I2C automáticamente en cada
ciclo — este es el patrón que evita la fuga. No hay forma de fechar cuándo se introdujo ese cambio
sin historial de git.

Nota: la fuga original (`calibration.json`) no es del bus I2C sino del archivo de calibración,
que se abre con `open(CALIBRACION_PATH) as f` (también un context manager) en
`cargar_calibracion()` — ya correctamente cerrado en el código actual también. Ambos puntos de
apertura de descriptores en el código vigente usan `with`, consistente con que el fix ya está
aplicado.

## ¿Existe un watchdog/heartbeat?

**No existe.** Se revisó todo el pipeline de alertas (`api/Controllers/mlController.js`,
`api/Services/alertNotifier.js`, `api/Controllers/alertController.js`): las únicas alertas
automáticas son las que dispara `notificarAnomalia()` cuando `mood` transiciona a
`atencion`/`critico` — es decir, dependen de que el servicio de ML seguía corriendo y evaluando
datos. **No hay ningún mecanismo que compare la antigüedad de la última lectura
(`lecturas.timestamp` o `ml_estado.updated_at`) contra un múltiplo de `SENSOR_INTERVALO_SEGUNDOS`
para avisar "no ha llegado una lectura nueva en k intervalos".** Esto explica por qué la brecha de
15.4 horas del 2026-08-24 no generó ninguna alerta explícita de "sensor caído": el sistema solo
alerta sobre anomalías en los valores, nunca sobre la ausencia de valores.

**Recomendación para el artículo/trabajo futuro:** agregar un chequeo de heartbeat (p. ej. en el
propio ciclo de `ml/service.py`, comparar `df["timestamp"].max()` contra `datetime.now()` y emitir
un mood/alerta especial si excede `k * SENSOR_INTERVALO_SEGUNDOS`) sería la forma más simple de
cerrar este hueco de observabilidad.
