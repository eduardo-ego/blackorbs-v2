# F1 — Prueba de tolerancia a desconexión del uplink (≥ 2 h)

Esta prueba requiere una acción física/manual (desconectar Tailscale/WiFi del dispositivo) que no
se puede ejecutar de forma remota ni automatizada desde esta sesión — si se desconecta el uplink,
también se pierde la conexión con la que se está leyendo este dispositivo. Aquí queda el
procedimiento documentado y el script de verificación posterior (`F_verificar_desconexion.py`),
listo para que el autor ejecute la desconexión física y luego corra el script.

## Procedimiento sugerido

1. Anotar la hora exacta de inicio (`T0`) antes de desconectar.
2. Desconectar el uplink por ≥ 2 horas. Opciones, de menor a mayor severidad:
   - Deshabilitar Tailscale: `sudo tailscale down` (revertir con `sudo tailscale up`).
   - Deshabilitar WiFi por completo: `sudo nmcli radio wifi off` (revertir con
     `sudo nmcli radio wifi on`).
   - Desconectar físicamente el dispositivo de red (si aplica).

   Importante: el sensor (`sensor/read_loop.py`) y el servicio de ML (`ml/service.py`) hacen sus
   POST a `http://localhost:3001/...`, **no** a través del uplink externo — dependen de que la API
   (`blackorbs-v2-api`) siga corriendo localmente, no de que haya salida a internet. Por lo tanto,
   cortar solo el uplink (Tailscale/WiFi) **no debería** interrumpir la ingesta de `lecturas` ni el
   ciclo de `ml_estado`, salvo que las notificaciones (Telegram/Teams/email, que sí requieren
   internet) se vean afectadas. Ver hipótesis abajo.
3. Anotar la hora exacta de reconexión (`T1`).
4. Correr `F_verificar_desconexion.py --inicio T0 --fin T1` (ajustar el rango si se prefiere pasar
   fechas ISO directamente).

## Qué verifica el script

- Que no falten lecturas en `lecturas` durante la ventana `[T0, T1]` (comparando el intervalo
  esperado ~60 s contra los timestamps reales, igual criterio que `B_brechas.py`).
- Que `ml_estado.updated_at` siguió avanzando durante la ventana (evidencia de que el ciclo de ML
  no se detuvo).
- Cuántas alertas (`alertas`) se generaron en la ventana, si las hubo.

## Hipótesis a confirmar (basada en la arquitectura, ver `A_herramientas_llm.md`/`F_fd_leak.md`)

- **Lecturas y `ml_estado`:** deberían seguir funcionando con normalidad, porque sensor → API → ML
  son todos loopback local (confirmado en `api/middleware/authGate.js`, que explícitamente permite
  `POST /data` y `POST /ml/update` sin sesión solo si la conexión es loopback).
- **Notificaciones (Telegram/Teams/email):** `api/Services/alertNotifier.js` llama a
  `bot.sendMessage(...)` (Telegram) y `sendTeamsAlert(...)` directamente, con
  `Promise.allSettled(...)` — es decir, **si fallan, el error se captura y se ignora (solo hay un
  `console.error`), no hay reintento automático ni cola de reintentos.** Si una alerta se genera
  durante el corte de uplink, quedará **registrada en la tabla `alertas`** (eso no depende de la
  red externa) pero **la notificación por Telegram/Teams se perderá silenciosamente** — no hay
  mecanismo de reintento en el código actual. Esto se puede confirmar empíricamente si durante la
  ventana de prueba se genera al menos una alerta real.
